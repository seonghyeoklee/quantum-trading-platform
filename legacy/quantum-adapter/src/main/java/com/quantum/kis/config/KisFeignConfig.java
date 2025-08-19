package com.quantum.kis.config;

import feign.Logger;
import feign.RequestInterceptor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** OpenFeign KIS API 클라이언트 설정 기본 헤더 정보만 중앙 관리 (순환 의존성 방지) */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class KisFeignConfig {

    private final KisRateLimitInterceptor rateLimitInterceptor;

    @Value("${kis.api.app-key}")
    private String appKey;

    @Value("${kis.api.app-secret}")
    private String appSecret;

    /** KIS API 기본 헤더 인터셉터 OAuth2 토큰 요청은 제외하고 일반 API 요청에만 적용 */
    @Bean
    public RequestInterceptor kisBasicHeaderInterceptor() {
        return template -> {
            // OAuth2 토큰 요청은 헤더에 appkey/appsecret 추가하지 않음 (바디에만)
            if (template.path().contains("/oauth2/tokenP")) {
                // Content-Type만 설정
                template.header("Content-Type", "application/json");
                log.debug("KIS: OAuth2 token request - headers excluded");
                return;
            }

            // 일반 API 요청에만 appkey, appsecret 헤더 추가
            template.header("appkey", appKey);
            template.header("appsecret", appSecret);

            // Content-Type은 POST 요청에만 추가
            if ("POST".equals(template.method())) {
                template.header("Content-Type", "application/json");
            }
        };
    }

    /** KIS API Rate Limiting 인터셉터는 @Component로 자동 등록됨 */

    /** Feign 로거 설정 - 헤더, 바디, 응답 모두 로깅 */
    @Bean
    public Logger.Level feignLoggerLevel() {
        return Logger.Level.FULL; // 요청/응답 헤더, 바디 모두 로깅
    }
}
