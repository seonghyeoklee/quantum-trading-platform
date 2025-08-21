package com.quantum.web.service;

import com.quantum.web.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * Authentication Service
 * 
 * 사용자 인증 관련 비즈니스 로직 처리
 * - 사용자 인증 및 토큰 발급
 * - 토큰 갱신 및 무효화
 * - 임시 사용자 데이터 관리 (Mock)
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final JwtTokenProvider jwtTokenProvider;
    private final PasswordEncoder passwordEncoder;
    private final RedisTemplate<String, Object> redisTemplate;

    // Mock 사용자 데이터 (실제로는 데이터베이스에서 조회)
    private static final Map<String, MockUser> MOCK_USERS = new HashMap<>();
    
    static {
        // 관리자 계정
        MOCK_USERS.put("admin", MockUser.builder()
                .id("USER-001")
                .username("admin")
                .name("시스템 관리자")
                .email("admin@quantum-trading.com")
                .password("$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.") // "password" 암호화
                .roles(Arrays.asList("ROLE_ADMIN", "ROLE_MANAGER", "ROLE_TRADER"))
                .enabled(true)
                .build());
                
        // 매니저 계정
        MOCK_USERS.put("manager", MockUser.builder()
                .id("USER-002")
                .username("manager")
                .name("포트폴리오 매니저")
                .email("manager@quantum-trading.com")
                .password("$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.") // "password" 암호화
                .roles(Arrays.asList("ROLE_MANAGER", "ROLE_TRADER"))
                .enabled(true)
                .build());
                
        // 트레이더 계정
        MOCK_USERS.put("trader", MockUser.builder()
                .id("USER-003")
                .username("trader")
                .name("퀀트 트레이더")
                .email("trader@quantum-trading.com")
                .password("$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.") // "password" 암호화
                .roles(Arrays.asList("ROLE_TRADER"))
                .enabled(true)
                .build());
    }

    /**
     * 사용자 인증 및 토큰 발급
     */
    public AuthResult authenticateUser(String username, String password) {
        // 사용자 조회
        MockUser user = MOCK_USERS.get(username.toLowerCase());
        
        if (user == null) {
            log.warn("Authentication failed - user not found: {}", username);
            throw new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + username);
        }
        
        if (!user.isEnabled()) {
            log.warn("Authentication failed - user disabled: {}", username);
            throw new IllegalArgumentException("비활성화된 계정입니다: " + username);
        }
        
        // 비밀번호 검증
        if (!passwordEncoder.matches(password, user.getPassword())) {
            log.warn("Authentication failed - invalid password for user: {}", username);
            throw new IllegalArgumentException("비밀번호가 올바르지 않습니다");
        }
        
        // JWT 토큰 생성
        String accessToken = jwtTokenProvider.generateAccessToken(
                user.getId(), user.getUsername(), user.getRoles());
        String refreshToken = jwtTokenProvider.generateRefreshToken(
                user.getId(), user.getUsername());
        
        // Refresh Token을 Redis에 저장 (7일 TTL)
        String refreshTokenKey = "refresh_token:" + user.getId();
        redisTemplate.opsForValue().set(refreshTokenKey, refreshToken, 7, TimeUnit.DAYS);
        
        log.info("User authenticated successfully - username: {}, roles: {}", 
                username, user.getRoles());
        
        return AuthResult.builder()
                .userId(user.getId())
                .username(user.getUsername())
                .name(user.getName())
                .email(user.getEmail())
                .roles(user.getRoles())
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .build();
    }

    /**
     * 토큰 갱신
     */
    public TokenPair refreshTokens(String userId, String username) {
        // 저장된 Refresh Token 검증
        String refreshTokenKey = "refresh_token:" + userId;
        String storedRefreshToken = (String) redisTemplate.opsForValue().get(refreshTokenKey);
        
        if (storedRefreshToken == null) {
            throw new IllegalArgumentException("Refresh Token이 만료되었거나 존재하지 않습니다");
        }
        
        // 사용자 정보 조회
        MockUser user = findUserById(userId);
        if (user == null) {
            throw new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + userId);
        }
        
        // 새로운 토큰 생성
        String newAccessToken = jwtTokenProvider.generateAccessToken(
                user.getId(), user.getUsername(), user.getRoles());
        String newRefreshToken = jwtTokenProvider.generateRefreshToken(
                user.getId(), user.getUsername());
        
        // 새로운 Refresh Token 저장
        redisTemplate.opsForValue().set(refreshTokenKey, newRefreshToken, 7, TimeUnit.DAYS);
        
        log.info("Tokens refreshed successfully - username: {}", username);
        
        return TokenPair.builder()
                .accessToken(newAccessToken)
                .refreshToken(newRefreshToken)
                .build();
    }

    /**
     * 토큰 무효화 (로그아웃)
     */
    public void invalidateToken(String token) {
        try {
            String userId = jwtTokenProvider.getUserIdFromToken(token);
            
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
            
            log.info("Token invalidated successfully - userId: {}", userId);
            
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
     * 사용자 ID로 사용자 조회
     */
    private MockUser findUserById(String userId) {
        return MOCK_USERS.values().stream()
                .filter(user -> user.getId().equals(userId))
                .findFirst()
                .orElse(null);
    }

    /**
     * 사용자명으로 사용자 조회
     */
    public MockUser findUserByUsername(String username) {
        return MOCK_USERS.get(username.toLowerCase());
    }

    /**
     * 모든 사용자 조회 (관리용)
     */
    public Collection<MockUser> getAllUsers() {
        return MOCK_USERS.values();
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
    
    // Mock User Entity
    
    @lombok.Builder
    @lombok.Data
    public static class MockUser {
        private String id;
        private String username;
        private String password;
        private String name;
        private String email;
        private List<String> roles;
        private boolean enabled;
        private LocalDateTime createdAt;
        private LocalDateTime lastLoginAt;
    }
}