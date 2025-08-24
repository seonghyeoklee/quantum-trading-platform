package com.quantum.web.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 전역 CORS 설정
 * 
 * 개발 환경에서 모든 Origin, 헤더, 메서드 허용
 */
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOriginPatterns("*") // 모든 Origin 허용
                .allowedMethods("*") // 모든 HTTP 메서드 허용
                .allowedHeaders("*") // 모든 헤더 허용
                .exposedHeaders("*") // 모든 헤더 노출
                .allowCredentials(true) // 인증정보 포함 허용
                .maxAge(86400); // 24시간 캐시
    }
}