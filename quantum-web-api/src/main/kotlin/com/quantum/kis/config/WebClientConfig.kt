package com.quantum.kis.config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.function.client.WebClient
import java.time.Duration

/**
 * WebClient 설정
 * 
 * KIS API 호출을 위한 WebClient 빈 등록
 */
@Configuration
class WebClientConfig {
    
    /**
     * 기본 WebClient 빈
     * KIS API 호출용으로 최적화된 설정
     */
    @Bean
    fun webClient(): WebClient {
        return WebClient.builder()
            .codecs { configurer ->
                // 응답 크기 제한 설정 (기본 256KB → 1MB)
                configurer.defaultCodecs().maxInMemorySize(1024 * 1024)
            }
            .build()
    }
}