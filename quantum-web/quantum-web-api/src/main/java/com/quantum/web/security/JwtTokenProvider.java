package com.quantum.web.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.stereotype.Component;
import com.quantum.web.security.UserPrincipal;

import javax.crypto.SecretKey;
import java.util.*;
import java.util.stream.Collectors;

/**
 * JWT Token Provider
 * 
 * JWT 토큰 생성, 검증, 파싱을 담당하는 서비스
 * - 사용자 인증 정보를 JWT로 변환
 * - 토큰에서 사용자 정보 및 권한 추출
 * - 토큰 유효성 검증
 */
@Slf4j
@Component
public class JwtTokenProvider {

    private static final String AUTHORITIES_KEY = "roles";
    private static final String USER_ID_KEY = "userId";
    private static final String USERNAME_KEY = "username";

    @Value("${app.jwt.secret:quantum-trading-secret-key-for-jwt-token-generation-must-be-at-least-256-bits}")
    private String jwtSecret;

    @Value("${app.jwt.access-token-expiration:86400000}") // 24시간 (밀리초)
    private long accessTokenExpiration;

    @Value("${app.jwt.refresh-token-expiration:604800000}") // 7일 (밀리초)  
    private long refreshTokenExpiration;

    private SecretKey secretKey;

    @PostConstruct
    protected void init() {
        secretKey = Keys.hmacShaKeyFor(jwtSecret.getBytes());
    }

    /**
     * Access Token 생성
     */
    public String generateAccessToken(String userId, String username, Collection<String> roles) {
        Date expiryDate = new Date(System.currentTimeMillis() + accessTokenExpiration);
        
        return Jwts.builder()
                .subject(username)
                .claim(USER_ID_KEY, userId)
                .claim(USERNAME_KEY, username)
                .claim(AUTHORITIES_KEY, String.join(",", roles))
                .issuedAt(new Date())
                .expiration(expiryDate)
                .signWith(secretKey)
                .compact();
    }

    /**
     * Refresh Token 생성
     */
    public String generateRefreshToken(String userId, String username) {
        Date expiryDate = new Date(System.currentTimeMillis() + refreshTokenExpiration);
        
        return Jwts.builder()
                .subject(username)
                .claim(USER_ID_KEY, userId)
                .claim(USERNAME_KEY, username)
                .issuedAt(new Date())
                .expiration(expiryDate)
                .signWith(secretKey)
                .compact();
    }

    /**
     * 토큰에서 사용자명 추출
     */
    public String getUsernameFromToken(String token) {
        Claims claims = getClaimsFromToken(token);
        return claims.get(USERNAME_KEY, String.class);
    }

    /**
     * 토큰에서 사용자 ID 추출
     */
    public String getUserIdFromToken(String token) {
        Claims claims = getClaimsFromToken(token);
        return claims.get(USER_ID_KEY, String.class);
    }

    /**
     * 토큰에서 권한 정보 추출
     */
    public Collection<GrantedAuthority> getAuthoritiesFromToken(String token) {
        Claims claims = getClaimsFromToken(token);
        String rolesString = claims.get(AUTHORITIES_KEY, String.class);
        
        if (rolesString == null || rolesString.trim().isEmpty()) {
            return Collections.emptyList();
        }
        
        return Arrays.stream(rolesString.split(","))
                .map(String::trim)
                .filter(role -> !role.isEmpty())
                .map(SimpleGrantedAuthority::new)
                .collect(Collectors.toList());
    }

    /**
     * 토큰으로부터 Authentication 객체 생성
     */
    public Authentication getAuthentication(String token) {
        String username = getUsernameFromToken(token);
        Collection<GrantedAuthority> authorities = getAuthoritiesFromToken(token);
        
        UserPrincipal principal = UserPrincipal.builder()
                .id(getUserIdFromToken(token))
                .username(username)
                .authorities(authorities)
                .build();
        
        return new UsernamePasswordAuthenticationToken(principal, token, authorities);
    }

    /**
     * 토큰 유효성 검증
     */
    public boolean validateToken(String token) {
        try {
            getClaimsFromToken(token);
            return true;
        } catch (ExpiredJwtException ex) {
            log.warn("JWT token is expired: {}", ex.getMessage());
        } catch (UnsupportedJwtException ex) {
            log.warn("JWT token is unsupported: {}", ex.getMessage());
        } catch (MalformedJwtException ex) {
            log.warn("JWT token is malformed: {}", ex.getMessage());
        } catch (SecurityException ex) {
            log.warn("JWT signature validation failed: {}", ex.getMessage());
        } catch (IllegalArgumentException ex) {
            log.warn("JWT token compact string is invalid: {}", ex.getMessage());
        } catch (Exception ex) {
            log.error("JWT token validation error: {}", ex.getMessage());
        }
        return false;
    }

    /**
     * 토큰 만료시간 확인
     */
    public Date getExpirationDateFromToken(String token) {
        Claims claims = getClaimsFromToken(token);
        return claims.getExpiration();
    }

    /**
     * 토큰 만료 여부 확인
     */
    public boolean isTokenExpired(String token) {
        Date expiration = getExpirationDateFromToken(token);
        return expiration.before(new Date());
    }

    /**
     * 토큰에서 Claims 추출 (공통 메서드)
     */
    private Claims getClaimsFromToken(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    /**
     * Bearer 토큰에서 실제 토큰 문자열 추출
     */
    public String extractTokenFromBearer(String bearerToken) {
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return bearerToken;
    }

    /**
     * 토큰 정보 요약 (디버깅용)
     */
    public Map<String, Object> getTokenInfo(String token) {
        try {
            Claims claims = getClaimsFromToken(token);
            Map<String, Object> info = new HashMap<>();
            info.put("username", claims.get(USERNAME_KEY));
            info.put("userId", claims.get(USER_ID_KEY));
            info.put("roles", claims.get(AUTHORITIES_KEY));
            info.put("issuedAt", claims.getIssuedAt());
            info.put("expiration", claims.getExpiration());
            info.put("isExpired", isTokenExpired(token));
            return info;
        } catch (Exception e) {
            log.error("Failed to extract token info: {}", e.getMessage());
            return Collections.emptyMap();
        }
    }
}