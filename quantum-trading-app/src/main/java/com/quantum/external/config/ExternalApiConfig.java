package com.quantum.external.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

/**
 * External API 설정
 */
@Configuration
@EnableConfigurationProperties(NaverNewsProperties.class)
public class ExternalApiConfig {

    /**
     * 외부 API 호출용 RestClient
     */
    @Bean
    public RestClient externalApiRestClient() {
        return RestClient.builder()
                .build();
    }

    /**
     * 네이버 뉴스 API 전용 RestClient
     */
    @Bean
    public RestClient naverNewsRestClient(NaverNewsProperties properties) {
        return RestClient.builder()
                .baseUrl(properties.baseUrl())
                .defaultHeader("X-Naver-Client-Id", properties.clientId())
                .defaultHeader("X-Naver-Client-Secret", properties.clientSecret())
                .build();
    }

    // TODO: DART API 설정
    // @Bean
    // public RestClient dartRestClient(DartProperties properties) { ... }

    // TODO: OpenAI API 설정
    // @Bean
    // public RestClient openAiRestClient(OpenAiProperties properties) { ... }
}
