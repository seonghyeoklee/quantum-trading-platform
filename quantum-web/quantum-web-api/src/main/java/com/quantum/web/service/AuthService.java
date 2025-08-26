package com.quantum.web.service;

import com.quantum.trading.platform.query.service.UserQueryService;
import com.quantum.trading.platform.query.view.UserView;
import com.quantum.trading.platform.shared.command.*;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.web.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import jakarta.servlet.http.HttpServletRequest;

import jakarta.annotation.PostConstruct;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * Authentication Service
 * 
 * Event-Driven 사용자 인증 관련 비즈니스 로직 처리
 * - Command Gateway를 통한 명령 전송
 * - Query Service를 통한 사용자 조회
 * - JWT 토큰 관리 및 Redis 세션 관리
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final CommandGateway commandGateway;
    private final UserQueryService userQueryService;
    private final JwtTokenProvider jwtTokenProvider;
    private final PasswordEncoder passwordEncoder;
    private final RedisTemplate<String, Object> redisTemplate;


    /**
     * 2FA가 필요한지 확인하는 초기 인증 (1단계)
     */
    public PreAuthResult preAuthenticate(String username, String password, HttpServletRequest request) {
        log.info("Pre-authentication for user: {}", username);
        
        // 기본 사용자 인증 로직 (기존과 동일)
        Optional<UserQueryService.UserLoginInfo> loginInfoOpt = userQueryService.findLoginInfo(username);
        if (loginInfoOpt.isEmpty()) {
            log.warn("Pre-authentication failed - user not found: {}", username);
            throw new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + username);
        }
        
        UserQueryService.UserLoginInfo loginInfo = loginInfoOpt.get();
        
        // 계정 상태 확인
        if (!loginInfo.canLogin()) {
            log.warn("Pre-authentication failed - user cannot login: {} (status: {}, attempts: {})", 
                    username, loginInfo.status(), loginInfo.failedLoginAttempts());
            throw new IllegalArgumentException("로그인할 수 없는 계정 상태입니다: " + loginInfo.status());
        }
        
        // 비밀번호 검증
        if (!passwordEncoder.matches(password, loginInfo.passwordHash())) {
            // 비밀번호 불일치 시 실패 Command 전송
            String clientIp = extractClientIp(request);
            String userAgent = extractUserAgent(request);
            
            RecordLoginFailureCommand failureCommand = new RecordLoginFailureCommand(
                    UserId.of(loginInfo.userId()),
                    "Invalid password",
                    clientIp,
                    userAgent
            );
            
            commandGateway.sendAndWait(failureCommand);
            throw new IllegalArgumentException("비밀번호가 올바르지 않습니다");
        }
        
        // 2FA 활성화 여부 확인
        UserView user = userQueryService.findByUsername(username)
                .orElseThrow(() -> new IllegalStateException("User not found after pre-authentication"));
        
        if (user.isTwoFactorEnabled()) {
            // 2FA가 필요한 경우, 임시 토큰 생성
            String tempToken = generateTempSessionToken(user.getUserId(), username);
            
            return PreAuthResult.builder()
                    .userId(user.getUserId())
                    .username(username)
                    .requiresTwoFactor(true)
                    .tempSessionToken(tempToken)
                    .build();
        } else {
            // 2FA가 필요하지 않은 경우, 바로 완전한 인증 수행
            return PreAuthResult.builder()
                    .userId(user.getUserId())
                    .username(username)
                    .requiresTwoFactor(false)
                    .authResult(completeAuthentication(user, request))
                    .build();
        }
    }

    /**
     * 사용자 인증 및 토큰 발급 (Event-Driven 방식) - 기존 메서드 (2FA 비활성화된 사용자용)
     */
    public AuthResult authenticateUser(String username, String password, HttpServletRequest request) {
        log.info("Attempting authentication for user: {}", username);
        
        // 디버깅을 위해 사용자 존재 여부 확인
        boolean userExists = userQueryService.isUsernameExists(username);
        log.info("Debug - User exists check: {} = {}", username, userExists);
        
        // 디버깅을 위해 모든 admin 사용자 조회
        Optional<UserQueryService.UserLoginInfo> loginInfoOpt = userQueryService.findLoginInfo(username);
        if (loginInfoOpt.isEmpty()) {
            // 비밀번호 해시 필터 없이 조회해보기
            Optional<UserView> userViewOpt = userQueryService.findByUsername(username);
            if (userViewOpt.isPresent()) {
                UserView userView = userViewOpt.get();
                log.warn("User found but no password hash: userId={}, username={}, passwordHash={}", 
                    userView.getUserId(), userView.getUsername(), userView.getPasswordHash());
            } else {
                log.warn("No user found at all for username: {}", username);
            }
        }
        
        // Query Side에서 사용자 조회
        UserQueryService.UserLoginInfo loginInfo;
        try {
            loginInfo = loginInfoOpt
                    .orElseThrow(() -> {
                        log.warn("Authentication failed - user not found: {} (userExists: {})", username, userExists);
                        return new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + username);
                    });
            log.info("Login info retrieved successfully: userId={}, username={}, status={}", 
                    loginInfo.userId(), loginInfo.username(), loginInfo.status());
        } catch (Exception e) {
            log.error("Error retrieving login info for user: {} - Error: {}", username, e.getMessage(), e);
            throw new IllegalArgumentException("사용자 정보 조회에 실패하였습니다: " + e.getMessage());
        }
        
        // 계정 상태 확인
        if (!loginInfo.canLogin()) {
            log.warn("Authentication failed - user cannot login: {} (status: {}, attempts: {})", 
                    username, loginInfo.status(), loginInfo.failedLoginAttempts());
            throw new IllegalArgumentException("로그인할 수 없는 계정 상태입니다: " + loginInfo.status());
        }
        
        // 세션 ID 생성
        String sessionId = "SESSION-" + UUID.randomUUID().toString();
        String clientIp = extractClientIp(request);
        String userAgent = extractUserAgent(request);
        
        try {
            // 저장된 사용자의 실제 비밀번호 해시를 사용하여 검증
            if (!passwordEncoder.matches(password, loginInfo.passwordHash())) {
                // 비밀번호 불일치 시 실패 Command 전송
                RecordLoginFailureCommand failureCommand = new RecordLoginFailureCommand(
                        UserId.of(loginInfo.userId()),
                        "Invalid password",
                        clientIp,
                        userAgent
                );
                
                commandGateway.sendAndWait(failureCommand);
                throw new IllegalArgumentException("비밀번호가 올바르지 않습니다");
            }
            
            // 비밀번호 검증 성공 시 로그인 성공 Command 전송 (비밀번호 필드는 빈 값)
            AuthenticateUserCommand authCommand = new AuthenticateUserCommand(
                    UserId.of(loginInfo.userId()),
                    username,
                    "", // 검증 완료된 상태이므로 빈 값
                    sessionId,
                    clientIp,
                    userAgent
            );
            
            // 인증 성공 명령 전송 (동기 방식)
            commandGateway.sendAndWait(authCommand);
            
            // 인증 성공 후 사용자 정보 재조회
            UserView user = userQueryService.findByUsername(username)
                    .orElseThrow(() -> new IllegalStateException("User not found after authentication"));
            
            // JWT 토큰 생성
            List<String> roles = new ArrayList<>(user.getRoles());
            String accessToken = jwtTokenProvider.generateAccessToken(
                    user.getUserId(), user.getUsername(), roles);
            String refreshToken = jwtTokenProvider.generateRefreshToken(
                    user.getUserId(), user.getUsername());
            
            // Refresh Token을 Redis에 저장 (7일 TTL)
            String refreshTokenKey = "refresh_token:" + user.getUserId();
            redisTemplate.opsForValue().set(refreshTokenKey, refreshToken, 7, TimeUnit.DAYS);
            
            log.info("User authenticated successfully - username: {}, roles: {}", 
                    username, user.getRoles());
            
            return AuthResult.builder()
                    .userId(user.getUserId())
                    .username(user.getUsername())
                    .name(user.getName())
                    .email(user.getEmail())
                    .roles(roles)
                    .accessToken(accessToken)
                    .refreshToken(refreshToken)
                    .build();
            
        } catch (Exception e) {
            // 인증 실패 시 실패 명령 전송 (선택적)
            log.warn("Authentication failed for user: {} - {}", username, e.getMessage());
            throw new IllegalArgumentException("인증에 실패하였습니다: " + e.getMessage());
        }
    }
    
    /**
     * HttpServletRequest에서 클라이언트 IP 추출
     */
    private String extractClientIp(HttpServletRequest request) {
        // 프록시를 통한 요청인 경우 원본 IP 확인
        String clientIp = request.getHeader("X-Forwarded-For");
        if (clientIp == null || clientIp.isEmpty() || "unknown".equalsIgnoreCase(clientIp)) {
            clientIp = request.getHeader("Proxy-Client-IP");
        }
        if (clientIp == null || clientIp.isEmpty() || "unknown".equalsIgnoreCase(clientIp)) {
            clientIp = request.getHeader("WL-Proxy-Client-IP");
        }
        if (clientIp == null || clientIp.isEmpty() || "unknown".equalsIgnoreCase(clientIp)) {
            clientIp = request.getHeader("HTTP_CLIENT_IP");
        }
        if (clientIp == null || clientIp.isEmpty() || "unknown".equalsIgnoreCase(clientIp)) {
            clientIp = request.getHeader("HTTP_X_FORWARDED_FOR");
        }
        if (clientIp == null || clientIp.isEmpty() || "unknown".equalsIgnoreCase(clientIp)) {
            clientIp = request.getRemoteAddr();
        }
        
        // X-Forwarded-For 헤더에서 첫 번째 IP만 추출 (체인된 경우)
        if (clientIp != null && clientIp.contains(",")) {
            clientIp = clientIp.split(",")[0].trim();
        }
        
        return clientIp != null ? clientIp : "unknown";
    }
    
    /**
     * HttpServletRequest에서 User-Agent 추출
     */
    private String extractUserAgent(HttpServletRequest request) {
        String userAgent = request.getHeader("User-Agent");
        return userAgent != null ? userAgent : "unknown";
    }

    /**
     * 토큰 갱신 (Event-Driven 방식)
     */
    public TokenPair refreshTokens(String userId, String username) {
        // 저장된 Refresh Token 검증
        String refreshTokenKey = "refresh_token:" + userId;
        String storedRefreshToken = (String) redisTemplate.opsForValue().get(refreshTokenKey);
        
        if (storedRefreshToken == null) {
            throw new IllegalArgumentException("Refresh Token이 만료되었거나 존재하지 않습니다");
        }
        
        // Query Side에서 사용자 정보 조회
        UserView user = userQueryService.findById(userId)
                .orElseThrow(() -> new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + userId));
        
        // 계정 상태 확인
        if (!user.canLogin()) {
            throw new IllegalArgumentException("로그인할 수 없는 계정 상태입니다: " + user.getStatus());
        }
        
        // 새로운 토큰 생성
        List<String> roles = new ArrayList<>(user.getRoles());
        String newAccessToken = jwtTokenProvider.generateAccessToken(
                user.getUserId(), user.getUsername(), roles);
        String newRefreshToken = jwtTokenProvider.generateRefreshToken(
                user.getUserId(), user.getUsername());
        
        // 새로운 Refresh Token 저장
        redisTemplate.opsForValue().set(refreshTokenKey, newRefreshToken, 7, TimeUnit.DAYS);
        
        log.info("Tokens refreshed successfully - username: {}", username);
        
        return TokenPair.builder()
                .accessToken(newAccessToken)
                .refreshToken(newRefreshToken)
                .build();
    }

    /**
     * 토큰 무효화 (로그아웃) - Event-Driven 방식
     */
    public void invalidateToken(String token, HttpServletRequest request) {
        try {
            String userId = jwtTokenProvider.getUserIdFromToken(token);
            String username = jwtTokenProvider.getUsernameFromToken(token);
            
            // Query Side에서 사용자 정보 조회하여 활성 세션 ID 가져오기
            String sessionId = userQueryService.findById(userId)
                    .map(userView -> userView.getActiveSessionId())
                    .orElse("UNKNOWN-SESSION");
            
            // Command를 통한 로그아웃 처리
            try {
                LogoutUserCommand logoutCommand = new LogoutUserCommand(
                        UserId.of(userId),
                        sessionId,
                        "USER_LOGOUT",
                        extractClientIp(request)
                );
                
                commandGateway.sendAndWait(logoutCommand);
                log.info("Logout command sent successfully for user: {}", username);
                
            } catch (Exception e) {
                log.warn("Failed to send logout command, continuing with token invalidation: {}", e.getMessage());
            }
            
            // Refresh Token 삭제
            String refreshTokenKey = "refresh_token:" + userId;
            redisTemplate.delete(refreshTokenKey);
            
            // Access Token 블랙리스트 추가 (토큰 만료까지)
            Date expiration = jwtTokenProvider.getExpirationDateFromToken(token);
            long ttl = expiration.getTime() - System.currentTimeMillis();
            
            if (ttl > 0) {
                String blacklistKey = "blacklist_token:" + token;
                redisTemplate.opsForValue().set(blacklistKey, "true", ttl, TimeUnit.MILLISECONDS);
            }
            
            log.info("Token invalidated successfully - userId: {}, username: {}", userId, username);
            
        } catch (Exception e) {
            log.error("Failed to invalidate token: {}", e.getMessage(), e);
        }
    }

    /**
     * 토큰 블랙리스트 확인
     */
    public boolean isTokenBlacklisted(String token) {
        String blacklistKey = "blacklist_token:" + token;
        return redisTemplate.hasKey(blacklistKey);
    }

    /**
     * 사용자 ID로 사용자 조회 (Event-Driven 방식)
     */
    public Optional<UserView> findUserById(String userId) {
        return userQueryService.findById(userId);
    }

    /**
     * 사용자명으로 사용자 조회 (Event-Driven 방식)
     */
    public Optional<UserView> findUserByUsername(String username) {
        return userQueryService.findByUsername(username);
    }

    /**
     * 모든 사용자 조회 (관리용) - Event-Driven 방식
     */
    public List<UserView> getAllUsers() {
        return userQueryService.findActiveUsers(); // 활성 사용자만 반환
    }
    
    /**
     * 사용자 등록 (Event-Driven 방식)
     */
    public String registerUser(String username, String password, String name, 
                             String email, String phone, Set<String> roles) {
        try {
            String userId = "USER-" + UUID.randomUUID().toString();
            String hashedPassword = passwordEncoder.encode(password); // 비밀번호 해시화
            
            RegisterUserCommand command = new RegisterUserCommand(
                    UserId.of(userId),
                    username,
                    hashedPassword, // 해시된 비밀번호
                    name,
                    email,
                    phone,
                    roles,
                    UserId.of("SYSTEM")
            );
            
            commandGateway.sendAndWait(command);
            
            log.info("User registered successfully: {} with ID: {}", username, userId);
            return userId;
            
        } catch (Exception e) {
            log.error("Failed to register user: {}", username, e);
            throw new IllegalArgumentException("사용자 등록에 실패하였습니다: " + e.getMessage());
        }
    }
    
    /**
     * 사용자 권한 부여 (Event-Driven 방식)
     */
    public void grantUserRole(String userId, String roleName, String grantedBy, String reason) {
        try {
            GrantUserRoleCommand command = new GrantUserRoleCommand(
                    UserId.of(userId),
                    roleName,
                    UserId.of(grantedBy),
                    reason
            );
            
            commandGateway.sendAndWait(command);
            
            log.info("Role granted successfully: {} to user: {} by: {}", roleName, userId, grantedBy);
            
        } catch (Exception e) {
            log.error("Failed to grant role: {} to user: {}", roleName, userId, e);
            throw new IllegalArgumentException("권한 부여에 실패하였습니다: " + e.getMessage());
        }
    }
    
    /**
     * 계정 잠금 (Event-Driven 방식)
     */
    public void lockUserAccount(String userId, String reason, String details, String lockedBy) {
        try {
            LockUserAccountCommand command = new LockUserAccountCommand(
                    UserId.of(userId),
                    reason,
                    details,
                    lockedBy != null ? UserId.of(lockedBy) : null
            );
            
            commandGateway.sendAndWait(command);
            
            log.info("Account locked successfully: {} by: {} - reason: {}", userId, lockedBy, reason);
            
        } catch (Exception e) {
            log.error("Failed to lock account: {}", userId, e);
            throw new IllegalArgumentException("계정 잠금에 실패하였습니다: " + e.getMessage());
        }
    }

    // Response DTOs
    
    @lombok.Builder
    @lombok.Data
    public static class AuthResult {
        private String userId;
        private String username;
        private String name;
        private String email;
        private List<String> roles;
        private String accessToken;
        private String refreshToken;
    }
    
    @lombok.Builder
    @lombok.Data
    public static class TokenPair {
        private String accessToken;
        private String refreshToken;
    }
    
    /**
     * 2FA 인증용 사용자 정보로 JWT 토큰 생성
     */
    public String generateTokenForUser(UserView user) {
        List<String> roles = new ArrayList<>(user.getRoles());
        return jwtTokenProvider.generateAccessToken(
                user.getUserId(), user.getUsername(), roles);
    }
    
    /**
     * 임시 세션 토큰 생성 (2FA 대기 중)
     */
    private String generateTempSessionToken(String userId, String username) {
        String tempToken = "TEMP-" + UUID.randomUUID().toString();
        
        // Redis에 임시 토큰 저장 (5분 TTL)
        String tempTokenKey = "temp_session:" + tempToken;
        Map<String, String> sessionData = new HashMap<>();
        sessionData.put("userId", userId);
        sessionData.put("username", username);
        sessionData.put("timestamp", String.valueOf(System.currentTimeMillis()));
        
        redisTemplate.opsForHash().putAll(tempTokenKey, sessionData);
        redisTemplate.expire(tempTokenKey, 5, TimeUnit.MINUTES);
        
        log.info("Temporary session token generated for user: {}", username);
        return tempToken;
    }
    
    /**
     * 임시 세션 토큰 검증 및 사용자 정보 반환
     */
    public TempSessionInfo validateTempSessionToken(String tempToken) {
        String tempTokenKey = "temp_session:" + tempToken;
        Map<Object, Object> sessionData = redisTemplate.opsForHash().entries(tempTokenKey);
        
        if (sessionData.isEmpty()) {
            throw new IllegalArgumentException("임시 세션이 만료되었거나 존재하지 않습니다");
        }
        
        String userId = (String) sessionData.get("userId");
        String username = (String) sessionData.get("username");
        
        return TempSessionInfo.builder()
                .userId(userId)
                .username(username)
                .tempToken(tempToken)
                .build();
    }
    
    /**
     * 임시 세션 토큰 제거
     */
    public void removeTempSessionToken(String tempToken) {
        String tempTokenKey = "temp_session:" + tempToken;
        redisTemplate.delete(tempTokenKey);
    }
    
    /**
     * 2FA 인증 완료 후 최종 인증 수행
     */
    private AuthResult completeAuthentication(UserView user, HttpServletRequest request) {
        // 세션 ID 생성
        String sessionId = "SESSION-" + UUID.randomUUID().toString();
        String clientIp = extractClientIp(request);
        String userAgent = extractUserAgent(request);
        
        try {
            // 로그인 성공 Command 전송
            AuthenticateUserCommand authCommand = new AuthenticateUserCommand(
                    UserId.of(user.getUserId()),
                    user.getUsername(),
                    "", // 이미 검증 완료
                    sessionId,
                    clientIp,
                    userAgent
            );
            
            commandGateway.sendAndWait(authCommand);
            
            // JWT 토큰 생성
            List<String> roles = new ArrayList<>(user.getRoles());
            String accessToken = jwtTokenProvider.generateAccessToken(
                    user.getUserId(), user.getUsername(), roles);
            String refreshToken = jwtTokenProvider.generateRefreshToken(
                    user.getUserId(), user.getUsername());
            
            // Refresh Token을 Redis에 저장 (7일 TTL)
            String refreshTokenKey = "refresh_token:" + user.getUserId();
            redisTemplate.opsForValue().set(refreshTokenKey, refreshToken, 7, TimeUnit.DAYS);
            
            log.info("Authentication completed successfully for user: {}", user.getUsername());
            
            return AuthResult.builder()
                    .userId(user.getUserId())
                    .username(user.getUsername())
                    .name(user.getName())
                    .email(user.getEmail())
                    .roles(roles)
                    .accessToken(accessToken)
                    .refreshToken(refreshToken)
                    .build();
                    
        } catch (Exception e) {
            log.error("Failed to complete authentication for user: {}", user.getUsername(), e);
            throw new IllegalArgumentException("인증 완료에 실패하였습니다: " + e.getMessage());
        }
    }
    
    // Additional DTOs for 2FA
    
    @lombok.Builder
    @lombok.Data
    public static class PreAuthResult {
        private String userId;
        private String username;
        private boolean requiresTwoFactor;
        private String tempSessionToken;
        private AuthResult authResult;
    }
    
    @lombok.Builder
    @lombok.Data
    public static class TempSessionInfo {
        private String userId;
        private String username;
        private String tempToken;
    }
}