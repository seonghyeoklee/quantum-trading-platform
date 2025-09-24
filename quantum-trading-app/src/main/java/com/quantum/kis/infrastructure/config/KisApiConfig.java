package com.quantum.kis.infrastructure.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

/**
 * KIS API 설정 클래스
 */
@Configuration
@EnableConfigurationProperties(KisConfig.class)
public class KisApiConfig {

    private final KisConfig config;

    public KisApiConfig(KisConfig config) {
        this.config = config;
    }

    /**
     * KIS API용 RestClient 빈 설정
     * @return RestClient 인스턴스
     */
    @Bean
    public RestClient restClient() {
        return RestClient.builder()
                .defaultHeader("User-Agent", config.getMyAgent())
                .build();
    }
}