package com.quantum.web.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * JWT Authentication Entry Point
 * 
 * 인증되지 않은 사용자가 보호된 리소스에 접근할 때 호출되는 핸들러
 * - 401 Unauthorized 응답 생성
 * - JSON 형태의 에러 응답 반환
 * - 로깅 및 보안 이벤트 기록
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper;

    @Override
    public void commence(HttpServletRequest request, 
                        HttpServletResponse response,
                        AuthenticationException authException) throws IOException, ServletException {
        
        // 요청 정보 로깅
        String requestUri = request.getRequestURI();
        String method = request.getMethod();
        String userAgent = request.getHeader("User-Agent");
        String clientIp = getClientIpAddress(request);
        
        log.warn("Unauthorized access attempt - Method: {}, URI: {}, IP: {}, UserAgent: {}, Error: {}", 
                method, requestUri, clientIp, userAgent, authException.getMessage());

        // 응답 설정
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");

        // 에러 응답 데이터 구성
        Map<String, Object> errorResponse = createErrorResponse(request, authException);

        // JSON 응답 작성
        response.getWriter().write(objectMapper.writeValueAsString(errorResponse));
    }

    /**
     * 에러 응답 데이터 생성
     */
    private Map<String, Object> createErrorResponse(HttpServletRequest request, AuthenticationException authException) {
        Map<String, Object> response = new HashMap<>();
        
        response.put("timestamp", LocalDateTime.now().toString());
        response.put("status", HttpServletResponse.SC_UNAUTHORIZED);
        response.put("error", "Unauthorized");
        response.put("message", getErrorMessage(authException));
        response.put("path", request.getRequestURI());
        
        // 추가 보안 정보 (개발환경에서만)
        if (isDebugMode()) {
            response.put("details", authException.getMessage());
            response.put("exceptionType", authException.getClass().getSimpleName());
        }
        
        return response;
    }

    /**
     * 사용자 친화적인 에러 메시지 생성
     */
    private String getErrorMessage(AuthenticationException authException) {
        String message = authException.getMessage();
        
        // 공통적인 인증 실패 케이스들
        if (message != null) {
            if (message.contains("expired")) {
                return "인증 토큰이 만료되었습니다. 다시 로그인해주세요.";
            } else if (message.contains("malformed") || message.contains("invalid")) {
                return "유효하지 않은 인증 토큰입니다.";
            } else if (message.contains("signature")) {
                return "인증 토큰의 서명이 유효하지 않습니다.";
            }
        }
        
        // 기본 메시지
        return "인증이 필요한 서비스입니다. 로그인 후 이용해주세요.";
    }

    /**
     * 클라이언트 IP 주소 추출 (프록시 고려)
     */
    private String getClientIpAddress(HttpServletRequest request) {
        // X-Forwarded-For 헤더 확인 (프록시/로드밸런서 사용 시)
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty() && !"unknown".equalsIgnoreCase(xForwardedFor)) {
            return xForwardedFor.split(",")[0].trim();
        }
        
        // X-Real-IP 헤더 확인
        String xRealIp = request.getHeader("X-Real-IP");
        if (xRealIp != null && !xRealIp.isEmpty() && !"unknown".equalsIgnoreCase(xRealIp)) {
            return xRealIp;
        }
        
        // 기본 RemoteAddr 사용
        return request.getRemoteAddr();
    }

    /**
     * 디버그 모드 확인 (개발환경 판단)
     */
    private boolean isDebugMode() {
        String profile = System.getProperty("spring.profiles.active", "");
        return profile.contains("dev") || profile.contains("local");
    }
}