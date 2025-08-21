package com.quantum.web.controller;

import com.quantum.web.security.JwtTokenProvider;
import com.quantum.web.security.UserPrincipal;
import com.quantum.web.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * Authentication Controller
 *
 * 사용자 인증 관련 API 엔드포인트
 * - 로그인/로그아웃
 * - 토큰 갱신
 * - 사용자 정보 조회
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
@Tag(name = "Authentication", description = "사용자 인증 관리 API")
public class AuthController {

    private final AuthService authService;
    private final JwtTokenProvider jwtTokenProvider;

    /**
     * 관리자 로그인
     */
    @PostMapping("/login")
    @Operation(summary = "관리자 로그인", description = "사용자명과 비밀번호로 로그인하여 JWT 토큰을 발급받습니다")
    public ResponseEntity<?> login(@Valid @RequestBody LoginRequest request, HttpServletRequest httpRequest) {

        try {
            log.info("Login attempt - username: {}, IP: {}",
                    request.username(), getClientIp(httpRequest));

            // 사용자 인증
            AuthService.AuthResult authResult = authService.authenticateUser(request.username(), request.password());

            log.info("Login successful - username: {}, roles: {}",
                    request.username(), authResult.getRoles());

            return ResponseEntity.ok(LoginResponse.builder()
                    .accessToken(authResult.getAccessToken())
                    .refreshToken(authResult.getRefreshToken())
                    .tokenType("Bearer")
                    .expiresIn(86400L) // 24시간
                    .user(UserInfo.builder()
                            .id(authResult.getUserId())
                            .username(authResult.getUsername())
                            .name(authResult.getName())
                            .email(authResult.getEmail())
                            .roles(authResult.getRoles())
                            .build())
                    .build());

        } catch (UsernameNotFoundException | IllegalArgumentException e) {
            log.warn("Login failed - username: {}, reason: {}", request.username(), e.getMessage());

            return ResponseEntity.badRequest().body(ErrorResponse.builder()
                    .error("INVALID_CREDENTIALS")
                    .message("사용자명 또는 비밀번호가 올바르지 않습니다.")
                    .timestamp(LocalDateTime.now())
                    .build());

        } catch (Exception e) {
            log.error("Login error - username: {}, error: {}", request.username(), e.getMessage(), e);

            return ResponseEntity.internalServerError().body(ErrorResponse.builder()
                    .error("AUTHENTICATION_ERROR")
                    .message("로그인 처리 중 오류가 발생했습니다.")
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    /**
     * 토큰 갱신
     */
    @PostMapping("/refresh")
    @Operation(summary = "토큰 갱신", description = "Refresh Token으로 새로운 Access Token을 발급받습니다")
    public ResponseEntity<?> refreshToken(@Valid @RequestBody RefreshTokenRequest request) {

        try {
            String refreshToken = request.refreshToken();

            // Refresh Token 검증
            if (!jwtTokenProvider.validateToken(refreshToken)) {
                return ResponseEntity.badRequest().body(ErrorResponse.builder()
                        .error("INVALID_REFRESH_TOKEN")
                        .message("유효하지 않은 Refresh Token입니다.")
                        .timestamp(LocalDateTime.now())
                        .build());
            }

            // 새로운 Access Token 발급
            String userId = jwtTokenProvider.getUserIdFromToken(refreshToken);
            String username = jwtTokenProvider.getUsernameFromToken(refreshToken);

            AuthService.TokenPair tokenPair = authService.refreshTokens(userId, username);

            log.info("Token refreshed successfully - username: {}", username);

            return ResponseEntity.ok(RefreshTokenResponse.builder()
                    .accessToken(tokenPair.getAccessToken())
                    .refreshToken(tokenPair.getRefreshToken())
                    .tokenType("Bearer")
                    .expiresIn(86400L) // 24시간
                    .build());

        } catch (Exception e) {
            log.error("Token refresh error: {}", e.getMessage(), e);

            return ResponseEntity.badRequest().body(ErrorResponse.builder()
                    .error("TOKEN_REFRESH_ERROR")
                    .message("토큰 갱신에 실패했습니다.")
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    /**
     * 현재 로그인한 사용자 정보 조회
     */
    @GetMapping("/me")
    @Operation(summary = "사용자 정보 조회", description = "현재 로그인한 사용자의 정보를 조회합니다")
    public ResponseEntity<?> getCurrentUser(@AuthenticationPrincipal UserPrincipal userPrincipal) {

        try {
            return ResponseEntity.ok(UserInfo.builder()
                    .id(userPrincipal.getId())
                    .username(userPrincipal.getUsername())
                    .name(userPrincipal.getName())
                    .email(userPrincipal.getEmail())
                    .roles(userPrincipal.getRoleNames())
                    .build());

        } catch (Exception e) {
            log.error("Get current user error: {}", e.getMessage(), e);

            return ResponseEntity.internalServerError().body(ErrorResponse.builder()
                    .error("USER_INFO_ERROR")
                    .message("사용자 정보 조회에 실패했습니다.")
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    /**
     * 로그아웃
     */
    @PostMapping("/logout")
    @Operation(summary = "로그아웃", description = "현재 세션을 종료하고 토큰을 무효화합니다")
    public ResponseEntity<?> logout(@AuthenticationPrincipal UserPrincipal userPrincipal,
                                   HttpServletRequest request) {

        try {
            String token = extractTokenFromRequest(request);

            // 토큰 블랙리스트 처리 (실제 구현에서는 Redis 등 사용)
            if (token != null) {
                authService.invalidateToken(token);
                log.info("User logged out - username: {}", userPrincipal.getUsername());
            }

            Map<String, Object> response = new HashMap<>();
            response.put("message", "로그아웃이 완료되었습니다.");
            response.put("timestamp", LocalDateTime.now());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("Logout error: {}", e.getMessage(), e);

            return ResponseEntity.internalServerError().body(ErrorResponse.builder()
                    .error("LOGOUT_ERROR")
                    .message("로그아웃 처리 중 오류가 발생했습니다.")
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    /**
     * 토큰 정보 조회 (디버깅용)
     */
    @GetMapping("/token/info")
    @Operation(summary = "토큰 정보 조회", description = "현재 토큰의 상세 정보를 조회합니다 (디버깅용)")
    public ResponseEntity<?> getTokenInfo(HttpServletRequest request) {

        try {
            String token = extractTokenFromRequest(request);

            if (token == null) {
                return ResponseEntity.badRequest().body(ErrorResponse.builder()
                        .error("NO_TOKEN")
                        .message("토큰이 제공되지 않았습니다.")
                        .timestamp(LocalDateTime.now())
                        .build());
            }

            Map<String, Object> tokenInfo = jwtTokenProvider.getTokenInfo(token);
            return ResponseEntity.ok(tokenInfo);

        } catch (Exception e) {
            log.error("Get token info error: {}", e.getMessage(), e);

            return ResponseEntity.badRequest().body(ErrorResponse.builder()
                    .error("TOKEN_INFO_ERROR")
                    .message("토큰 정보 조회에 실패했습니다.")
                    .timestamp(LocalDateTime.now())
                    .build());
        }
    }

    // Helper methods

    private String getClientIp(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty()) {
            return xForwardedFor.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }

    private String extractTokenFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        return jwtTokenProvider.extractTokenFromBearer(bearerToken);
    }

    // Request/Response DTOs

    public record LoginRequest(
            @NotBlank(message = "사용자명을 입력해주세요") String username,
            @NotBlank(message = "비밀번호를 입력해주세요") String password
    ) {}

    public record RefreshTokenRequest(
            @NotBlank(message = "Refresh Token을 입력해주세요") String refreshToken
    ) {}

    @lombok.Builder
    public record LoginResponse(
            String accessToken,
            String refreshToken,
            String tokenType,
            Long expiresIn,
            UserInfo user
    ) {}

    @lombok.Builder
    public record RefreshTokenResponse(
            String accessToken,
            String refreshToken,
            String tokenType,
            Long expiresIn
    ) {}

    @lombok.Builder
    public record UserInfo(
            String id,
            String username,
            String name,
            String email,
            Object roles
    ) {}

    @lombok.Builder
    public record ErrorResponse(
            String error,
            String message,
            LocalDateTime timestamp
    ) {}
}
