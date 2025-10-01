package com.quantum.external.infrastructure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * DART API 설정
 */
@ConfigurationProperties(prefix = "dart")
public record DartProperties(
        String apiKey,
        String baseUrl
) {
    public DartProperties {
        if (baseUrl == null || baseUrl.isBlank()) {
            baseUrl = "https://opendart.fss.or.kr";
        }
    }
}
