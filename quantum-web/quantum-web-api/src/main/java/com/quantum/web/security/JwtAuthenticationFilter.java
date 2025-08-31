package com.quantum.web.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * JWT Authentication Filter
 * 
 * 모든 HTTP 요청에 대해 JWT 토큰 검증을 수행하는 필터
 * - Authorization 헤더에서 JWT 토큰 추출
 * - 토큰 유효성 검증 및 사용자 인증 정보 설정
 * - SecurityContext에 Authentication 객체 저장
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    private final JwtTokenProvider jwtTokenProvider;
    private final RedisTemplate<String, Object> redisTemplate;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request, 
            HttpServletResponse response, 
            FilterChain filterChain) throws ServletException, IOException {

        try {
            // 1. 요청에서 JWT 토큰 추출
            String token = extractTokenFromRequest(request);
            
            // 2. 토큰이 있고 유효한지 검증 (블랙리스트 확인 포함)
            if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token) && !isTokenBlacklisted(token)) {
                
                // 3. 토큰에서 인증 정보 생성
                Authentication authentication = jwtTokenProvider.getAuthentication(token);
                
                // 4. SecurityContext에 인증 정보 설정
                SecurityContextHolder.getContext().setAuthentication(authentication);
                
                // 로깅 (디버그 레벨)
                if (log.isDebugEnabled()) {
                    UserPrincipal principal = (UserPrincipal) authentication.getPrincipal();
                    log.debug("Successfully authenticated user: {} with roles: {}", 
                             principal.getUsername(), 
                             principal.getAuthorities());
                }
            } else if (StringUtils.hasText(token) && isTokenBlacklisted(token)) {
                log.warn("Blacklisted token attempted to access: {}", request.getRequestURI());
            }
            
        } catch (Exception e) {
            // JWT 처리 중 예외 발생 시 로깅 (SecurityContext 클리어)
            log.error("JWT authentication failed: {}", e.getMessage());
            SecurityContextHolder.clearContext();
        }

        // 다음 필터로 요청 전달
        filterChain.doFilter(request, response);
    }

    /**
     * HTTP 요청에서 JWT 토큰 추출
     */
    private String extractTokenFromRequest(HttpServletRequest request) {
        // Authorization 헤더에서 토큰 추출
        String bearerToken = request.getHeader(AUTHORIZATION_HEADER);
        
        // 디버깅용 로그 추가 (actuator 경로 완전 제외)
        String requestURI = request.getRequestURI();
        if (!requestURI.startsWith("/actuator/") && !requestURI.equals("/api/health") && requestURI.startsWith("/api/")) {
            log.debug("[JWT Filter] Request URI: {}, Authorization header: {}", 
                     requestURI, 
                     bearerToken != null ? bearerToken.substring(0, Math.min(20, bearerToken.length())) + "..." : "NULL");
        }
        
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith(BEARER_PREFIX)) {
            String token = bearerToken.substring(BEARER_PREFIX.length());
            log.debug("[JWT Filter] Extracted token: {}...", token.substring(0, Math.min(20, token.length())));
            return token;
        } else {
            log.debug("[JWT Filter] No valid Bearer token found in Authorization header");
        }
        
        // 쿠키에서 토큰 추출 (선택적)
        // Cookie[] cookies = request.getCookies();
        // if (cookies != null) {
        //     for (Cookie cookie : cookies) {
        //         if ("accessToken".equals(cookie.getName())) {
        //             return cookie.getValue();
        //         }
        //     }
        // }
        
        return null;
    }

    /**
     * 토큰 블랙리스트 확인
     */
    private boolean isTokenBlacklisted(String token) {
        try {
            String blacklistKey = "blacklist_token:" + token;
            return redisTemplate.hasKey(blacklistKey);
        } catch (Exception e) {
            log.error("Failed to check token blacklist: {}", e.getMessage());
            return false; // Redis 연결 실패 시 토큰을 유효한 것으로 처리
        }
    }

    /**
     * 필터를 건너뛸 경로 판단 (성능 최적화)
     */
    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) throws ServletException {
        String path = request.getRequestURI();
        
        // actuator 경로는 완전히 건너뛰기 (로그 없이)
        if (path.startsWith("/actuator/")) {
            return true;
        }
        
        boolean shouldSkip = path.equals("/api/v1/auth/login") ||
               path.equals("/api/v1/auth/refresh") ||
               path.equals("/api/v1/auth/logout") ||
               path.startsWith("/swagger-ui/") ||
               path.startsWith("/v3/api-docs/") ||
               path.equals("/api/health") ||
               path.startsWith("/ws/"); // WebSocket handshake
        
        // 디버깅용 로그 완전히 비활성화 (반복적인 로그 방지)
        
        return shouldSkip;
    }
}