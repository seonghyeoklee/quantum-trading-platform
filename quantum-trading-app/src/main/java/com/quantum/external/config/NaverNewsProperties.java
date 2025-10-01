package com.quantum.external.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * 네이버 뉴스 API 설정
 */
@ConfigurationProperties(prefix = "naver.news")
public record NaverNewsProperties(
        String clientId,
        String clientSecret,
        String baseUrl
) {
    public NaverNewsProperties {
        // 기본값 설정
        if (baseUrl == null || baseUrl.isEmpty()) {
            baseUrl = "https://openapi.naver.com/v1/search";
        }
    }
}
