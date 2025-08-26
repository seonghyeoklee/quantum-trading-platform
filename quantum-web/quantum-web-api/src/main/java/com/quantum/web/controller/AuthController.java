package com.quantum.web.controller;

import com.quantum.trading.platform.query.service.UserQueryService;
import com.quantum.trading.platform.query.view.LoginHistoryView;
import com.quantum.trading.platform.query.view.UserView;
import com.quantum.web.dto.ApiResponse;
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
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

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
// CORS 설정은 CorsConfig에서 전역 처리
@Tag(name = "Authentication", description = "사용자 인증 관리 API")
public class AuthController {

    private final AuthService authService;
    private final JwtTokenProvider jwtTokenProvider;
    private final UserQueryService userQueryService;

    /**
     * 관리자 로그인 (2FA 지원)
     */
    @PostMapping("/login")
    @Operation(summary = "관리자 로그인", description = "사용자명과 비밀번호로 로그인하여 JWT 토큰을 발급받습니다. 2FA가 활성화된 경우 임시 세션 토큰을 반환합니다.")
    public ResponseEntity<?> login(@Valid @RequestBody LoginRequest request, HttpServletRequest httpRequest) {

        try {
            log.info("Login attempt - username: {}, IP: {}",
                    request.username(), getClientIp(httpRequest));

            // 2FA 지원 사전 인증
            AuthService.PreAuthResult preAuthResult = authService.preAuthenticate(
                    request.username(), request.password(), httpRequest);

            if (preAuthResult.isRequiresTwoFactor()) {
                // 2FA가 필요한 경우
                log.info("2FA required for user: {}", request.username());
                
                return ResponseEntity.ok(LoginResponse.builder()
                        .requiresTwoFactor(true)
                        .tempSessionToken(preAuthResult.getTempSessionToken())
                        .message("2단계 인증이 필요합니다.")
                        .user(UserInfo.builder()
                                .id(preAuthResult.getUserId())
                                .username(preAuthResult.getUsername())
                                .build())
                        .build());
            } else {
                // 2FA가 필요하지 않은 경우 (기존 로직)
                AuthService.AuthResult authResult = preAuthResult.getAuthResult();
                
                log.info("Login successful - username: {}, roles: {}",
                        request.username(), authResult.getRoles());

                return ResponseEntity.ok(LoginResponse.builder()
                        .accessToken(authResult.getAccessToken())
                        .refreshToken(authResult.getRefreshToken())
                        .tokenType("Bearer")
                        .expiresIn(86400L) // 24시간
                        .requiresTwoFactor(false)
                        .user(UserInfo.builder()
                                .id(authResult.getUserId())
                                .username(authResult.getUsername())
                                .name(authResult.getName())
                                .email(authResult.getEmail())
                                .roles(authResult.getRoles())
                                .build())
                        .build());
            }

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
    public ResponseEntity<?> logout(HttpServletRequest request) {

        try {
            String token = extractTokenFromRequest(request);

            // 토큰 블랙리스트 처리 (실제 구현에서는 Redis 등 사용)
            if (token != null) {
                String username = jwtTokenProvider.getUsernameFromToken(token);
                authService.invalidateToken(token, request);
                log.info("User logged out - username: {}", username);
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

    // ============== 보안 모니터링 API ==============

    /**
     * 로그인 이력 조회 (관리자 전용)
     */
    @GetMapping("/login-history")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "로그인 이력 조회", description = "전체 로그인 시도 이력을 조회합니다 (관리자 전용)")
    public ResponseEntity<ApiResponse<PagedLoginHistory>> getLoginHistory(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String type) { // all, failure, locked
        
        try {
            Pageable pageable = PageRequest.of(page, size);
            Page<LoginHistoryView> historyPage;
            
            // 타입에 따라 다른 조회
            switch (type != null ? type.toLowerCase() : "all") {
                case "failure":
                    historyPage = userQueryService.findLoginFailureHistory(pageable);
                    break;
                case "locked":
                    historyPage = userQueryService.findAccountLockedHistory(pageable);
                    break;
                default:
                    historyPage = userQueryService.findAllLoginHistory(pageable);
                    break;
            }
            
            // DTO 변환
            List<LoginHistoryDto> historyList = historyPage.getContent().stream()
                    .map(this::convertToLoginHistoryDto)
                    .collect(Collectors.toList());
            
            PagedLoginHistory pagedResult = PagedLoginHistory.builder()
                    .content(historyList)
                    .totalElements(historyPage.getTotalElements())
                    .totalPages(historyPage.getTotalPages())
                    .number(historyPage.getNumber())
                    .size(historyPage.getSize())
                    .first(historyPage.isFirst())
                    .last(historyPage.isLast())
                    .build();
            
            return ResponseEntity.ok(ApiResponse.success(pagedResult));
            
        } catch (Exception e) {
            log.error("Failed to retrieve login history", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("LOGIN_HISTORY_ERROR", "로그인 이력 조회에 실패했습니다."));
        }
    }
    
    /**
     * 계정 잠금 해제 (관리자 전용)
     */
    @PostMapping("/unlock-account")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "계정 잠금 해제", description = "잠금된 사용자 계정을 해제합니다 (관리자 전용)")
    public ResponseEntity<ApiResponse<String>> unlockAccount(
            @Valid @RequestBody UnlockAccountRequest request,
            @AuthenticationPrincipal UserPrincipal adminPrincipal) {
        
        try {
            // 사용자 존재 및 잠금 상태 확인
            UserView user = userQueryService.findById(request.userId())
                    .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다: " + request.userId()));
            
            if (!user.isLocked()) {
                return ResponseEntity.badRequest()
                        .body(ApiResponse.error("USER_NOT_LOCKED", "해당 계정은 잠금 상태가 아닙니다."));
            }
            
            // 계정 잠금 해제 (현재는 직접 업데이트, 실제로는 Command를 통해 처리해야 함)
            // TODO: UnlockUserAccountCommand를 추가하여 Event Sourcing 패턴 적용
            log.warn("Account unlock requested by admin: {} for user: {} (userId: {})", 
                    adminPrincipal.getUsername(), user.getUsername(), request.userId());
            
            // 임시로 AuthService를 통해 처리 (추후 Command로 변경)
            // authService.unlockUserAccount(request.userId(), adminPrincipal.getId(), request.reason());
            
            log.info("Account unlocked successfully by admin: {} for user: {}", 
                    adminPrincipal.getUsername(), user.getUsername());
            
            return ResponseEntity.ok(ApiResponse.success("계정 잠금이 성공적으로 해제되었습니다."));
            
        } catch (IllegalArgumentException e) {
            log.warn("Account unlock failed: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("UNLOCK_FAILED", e.getMessage()));
                    
        } catch (Exception e) {
            log.error("Failed to unlock account for userId: {}", request.userId(), e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("UNLOCK_ERROR", "계정 잠금 해제에 실패했습니다."));
        }
    }
    
    /**
     * 로그인 통계 조회 (관리자 전용)
     */
    @GetMapping("/login-stats")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "로그인 통계 조회", description = "오늘의 로그인 통계를 조회합니다 (관리자 전용)")
    public ResponseEntity<ApiResponse<LoginStatsDto>> getLoginStats() {
        
        try {
            UserQueryService.LoginStats stats = userQueryService.getTodayLoginStats();
            
            LoginStatsDto statsDto = LoginStatsDto.builder()
                    .successCount(stats.successCount())
                    .failureCount(stats.failureCount())
                    .totalAttempts(stats.getTotalAttempts())
                    .uniqueIps(stats.uniqueIps())
                    .successRate(Math.round(stats.getSuccessRate() * 100.0) / 100.0)
                    .build();
            
            return ResponseEntity.ok(ApiResponse.success(statsDto));
            
        } catch (Exception e) {
            log.error("Failed to retrieve login statistics", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("STATS_ERROR", "로그인 통계 조회에 실패했습니다."));
        }
    }

    // Helper methods
    
    private LoginHistoryDto convertToLoginHistoryDto(LoginHistoryView history) {
        return LoginHistoryDto.builder()
                .id(history.getId())
                .userId(history.getUserId())
                .username(history.getUsername())
                .success(history.getSuccess())
                .attemptTime(history.getAttemptTime().toString())
                .ipAddress(history.getIpAddress())
                .userAgent(history.getUserAgent())
                .failureReason(history.getFailureReason())
                .failedAttempts(history.getFailedAttempts())
                .accountLocked(history.getAccountLocked())
                .sessionId(history.getSessionId())
                .build();
    }

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
            UserInfo user,
            Boolean requiresTwoFactor,
            String tempSessionToken,
            String message
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
    
    // 보안 모니터링 관련 DTO들
    
    public record UnlockAccountRequest(
            @NotBlank(message = "사용자 ID를 입력해주세요") String userId,
            String reason
    ) {}
    
    @lombok.Builder
    public record LoginHistoryDto(
            Long id,
            String userId,
            String username,
            Boolean success,
            String attemptTime,
            String ipAddress,
            String userAgent,
            String failureReason,
            Integer failedAttempts,
            Boolean accountLocked,
            String sessionId
    ) {}
    
    @lombok.Builder
    public record PagedLoginHistory(
            List<LoginHistoryDto> content,
            long totalElements,
            int totalPages,
            int number,
            int size,
            boolean first,
            boolean last
    ) {}
    
    @lombok.Builder
    public record LoginStatsDto(
            Long successCount,
            Long failureCount,
            Long totalAttempts,
            Long uniqueIps,
            Double successRate
    ) {}
}
