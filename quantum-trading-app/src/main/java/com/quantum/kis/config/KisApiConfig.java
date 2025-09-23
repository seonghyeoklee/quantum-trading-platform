package com.quantum.kis.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

/**
 * KIS API 설정 클래스
 */
@Configuration
@EnableConfigurationProperties(KisConfigProperties.class)
public class KisApiConfig {

    private final KisConfigProperties properties;

    public KisApiConfig(KisConfigProperties properties) {
        this.properties = properties;
    }

    /**
     * KIS API용 RestClient 빈 설정
     * @return RestClient 인스턴스
     */
    @Bean
    public RestClient restClient() {
        return RestClient.builder()
                .defaultHeader("User-Agent", properties.myAgent())
                .build();
    }

    /**
     * KisConfig 빈 설정
     * @return KisConfig 인스턴스
     */
    @Bean
    public KisConfig kisConfig() {
        return properties.toKisConfig();
    }
}