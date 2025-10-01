package com.quantum.external.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

/**
 * External API 설정
 * TODO: 각 API별 설정 추가
 */
@Configuration
public class ExternalApiConfig {

    /**
     * 외부 API 호출용 RestClient
     * TODO: 필요시 API별로 별도 RestClient 생성
     */
    @Bean
    public RestClient externalApiRestClient() {
        return RestClient.builder()
                .build();
    }

    // TODO: 네이버 API 설정
    // @Bean
    // public NaverApiConfig naverApiConfig() { ... }

    // TODO: DART API 설정
    // @Bean
    // public DartApiConfig dartApiConfig() { ... }

    // TODO: OpenAI API 설정
    // @Bean
    // public OpenAiApiConfig openAiApiConfig() { ... }
}
