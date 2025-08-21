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
     * 시스템 초기화 시 기본 사용자 생성
     * ApplicationReadyEvent로 Command Handler 등록 후 실행
     */
    @EventListener(ApplicationReadyEvent.class)
    public void initializeDefaultUsers() {
        log.info("Initializing default users...");
        
        // Event Store에서 이벤트 재생이 완료될 때까지 잠시 대기
        try {
            Thread.sleep(2000); // 2초 대기
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        
        try {
            
            // 관리자 계정 생성 (새 ID 사용하여 기존 이벤트와 충돌 방지)
            createDefaultUserIfNotExists("USER-101", "admin", "admin123", "시스템 관리자", 
                    "admin@quantum-trading.com", "010-0000-0001",
                    Set.of("ROLE_ADMIN", "ROLE_MANAGER", "ROLE_TRADER"));
            
            // 매니저 계정 생성  
            createDefaultUserIfNotExists("USER-102", "manager", "manager123", "포트폴리오 매니저",
                    "manager@quantum-trading.com", "010-0000-0002", 
                    Set.of("ROLE_MANAGER", "ROLE_TRADER"));
            
            // 트레이더 계정 생성
            createDefaultUserIfNotExists("USER-103", "trader", "trader123", "퀀트 트레이더",
                    "trader@quantum-trading.com", "010-0000-0003",
                    Set.of("ROLE_TRADER"));
                    
        } catch (Exception e) {
            log.error("Error during user initialization", e);
        }
    }
    
    private void createDefaultUserIfNotExists(String userId, String username, String password, String name,
                                            String email, String phone, Set<String> roles) {
        // 사용자가 존재하지만 비밀번호 해시가 없는 경우도 고려
        Optional<UserQueryService.UserLoginInfo> loginInfo = userQueryService.findLoginInfo(username);
        
        if (loginInfo.isEmpty()) {
            // 사용자가 존재하지 않거나 비밀번호 해시가 없는 경우 새로 생성
            try {
                String hashedPassword = passwordEncoder.encode(password); // 사용자별 비밀번호 해시화
                RegisterUserCommand command = RegisterUserCommand.builder()
                        .userId(UserId.of(userId))
                        .username(username)
                        .password(hashedPassword) // 해시된 비밀번호
                        .name(name)
                        .email(email)
                        .phone(phone)
                        .initialRoles(roles)
                        .registeredBy(UserId.of("SYSTEM"))
                        .build();
                
                commandGateway.sendAndWait(command);
                log.info("Default user created: {}", username);
            } catch (Exception e) {
                log.error("Failed to create default user: {}", username, e);
            }
        } else {
            log.info("Default user already exists with valid password hash: {}", username);
        }
    }

    /**
     * 사용자 인증 및 토큰 발급 (Event-Driven 방식)
     */
    public AuthResult authenticateUser(String username, String password) {
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
        UserQueryService.UserLoginInfo loginInfo = loginInfoOpt
                .orElseThrow(() -> {
                    log.warn("Authentication failed - user not found: {} (userExists: {})", username, userExists);
                    return new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + username);
                });
        
        // 계정 상태 확인
        if (!loginInfo.canLogin()) {
            log.warn("Authentication failed - user cannot login: {} (status: {}, attempts: {})", 
                    username, loginInfo.status(), loginInfo.failedLoginAttempts());
            throw new IllegalArgumentException("로그인할 수 없는 계정 상태입니다: " + loginInfo.status());
        }
        
        // 세션 ID 생성
        String sessionId = "SESSION-" + UUID.randomUUID().toString();
        String clientIp = getCurrentClientIp(); // 실제 구현에서는 HttpServletRequest에서 IP 추출
        String userAgent = getCurrentUserAgent(); // 실제 구현에서는 HttpServletRequest에서 User-Agent 추출
        
        try {
            // 저장된 사용자의 실제 비밀번호 해시를 사용하여 검증
            if (!passwordEncoder.matches(password, loginInfo.passwordHash())) {
                // 비밀번호 불일치 시 실패 Command 전송
                RecordLoginFailureCommand failureCommand = RecordLoginFailureCommand.builder()
                        .userId(UserId.of(loginInfo.userId()))
                        .reason("Invalid password")
                        .ipAddress(clientIp)
                        .userAgent(userAgent)
                        .build();
                
                commandGateway.sendAndWait(failureCommand);
                throw new IllegalArgumentException("비밀번호가 올바르지 않습니다");
            }
            
            // 비밀번호 검증 성공 시 로그인 성공 Command 전송 (비밀번호 필드는 빈 값)
            AuthenticateUserCommand authCommand = AuthenticateUserCommand.builder()
                    .userId(UserId.of(loginInfo.userId()))
                    .username(username)
                    .password("") // 검증 완료된 상태이므로 빈 값
                    .sessionId(sessionId)
                    .ipAddress(clientIp)
                    .userAgent(userAgent)
                    .build();
            
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
     * 현재 클라이언트 IP 조회 (임시 구현)
     */
    private String getCurrentClientIp() {
        // 실제 구현에서는 HttpServletRequest에서 IP 추출
        return "127.0.0.1";
    }
    
    /**
     * 현재 사용자 에이전트 조회 (임시 구현)
     */
    private String getCurrentUserAgent() {
        // 실제 구현에서는 HttpServletRequest에서 User-Agent 추출
        return "Quantum-Trading-Platform/1.0";
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
    public void invalidateToken(String token) {
        try {
            String userId = jwtTokenProvider.getUserIdFromToken(token);
            String username = jwtTokenProvider.getUsernameFromToken(token);
            
            // Query Side에서 사용자 세션 정보 조회
            UserQueryService.UserSessionInfo sessionInfo = userQueryService.findSessionInfo(token)
                    .orElse(null);
            
            String sessionId = sessionInfo != null ? "SESSION-FROM-TOKEN" : "UNKNOWN-SESSION";
            
            // Command를 통한 로그아웃 처리
            try {
                LogoutUserCommand logoutCommand = LogoutUserCommand.builder()
                        .userId(UserId.of(userId))
                        .sessionId(sessionId)
                        .reason("USER_LOGOUT")
                        .ipAddress(getCurrentClientIp())
                        .build();
                
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
            
            RegisterUserCommand command = RegisterUserCommand.builder()
                    .userId(UserId.of(userId))
                    .username(username)
                    .password(hashedPassword) // 해시된 비밀번호
                    .name(name)
                    .email(email)
                    .phone(phone)
                    .initialRoles(roles)
                    .registeredBy(UserId.of("SYSTEM"))
                    .build();
            
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
            GrantUserRoleCommand command = GrantUserRoleCommand.builder()
                    .userId(UserId.of(userId))
                    .roleName(roleName)
                    .grantedBy(UserId.of(grantedBy))
                    .reason(reason)
                    .build();
            
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
            LockUserAccountCommand command = LockUserAccountCommand.builder()
                    .userId(UserId.of(userId))
                    .reason(reason)
                    .details(details)
                    .lockedBy(lockedBy != null ? UserId.of(lockedBy) : null)
                    .build();
            
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
}