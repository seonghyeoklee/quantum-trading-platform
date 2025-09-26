package com.quantum.kis.infrastructure.config;

import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.application.port.out.KisTokenRepositoryPort;
import com.quantum.kis.application.port.out.NotificationPort;
import com.quantum.kis.infrastructure.adapter.out.kis.KisApiAdapter;
import com.quantum.kis.infrastructure.adapter.out.notification.LoggingNotificationAdapter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;
import com.quantum.kis.infrastructure.config.KisConfig;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * KIS 모듈의 헥사고날 아키텍처 Bean 설정
 * 포트와 어댑터 간의 의존성 주입을 설정
 */
@Configuration
public class KisHexagonalConfiguration {

    /**
     * KIS API 포트 구현체 빈 등록
     */
    @Bean
    public KisApiPort kisApiPort(RestClient restClient, KisConfig config, ObjectMapper objectMapper,
                               KisTokenRepositoryPort kisTokenRepositoryPort) {
        return new KisApiAdapter(restClient, config, objectMapper, kisTokenRepositoryPort);
    }


    /**
     * 알림 포트 구현체 빈 등록
     */
    @Bean
    public NotificationPort notificationPort() {
        return new LoggingNotificationAdapter();
    }
}