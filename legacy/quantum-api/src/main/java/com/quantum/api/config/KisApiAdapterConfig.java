package com.quantum.api.config;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * quantum-adapter 모듈의 컴포넌트를 quantum-api에서 사용하기 위한 설정
 *
 * <p>KIS API 클라이언트, 멀티 조회 서비스, Rate Limiter를 Bean으로 등록
 */
@Configuration
@EnableScheduling // KisRateLimiter의 @Scheduled 메서드 활성화
@ComponentScan(
        basePackages = {
            "com.quantum.kis.service", // KisRateLimiter, KisMultiStockPriceService
            "com.quantum.kis.config", // KisApiRateLimitConfig, KisFeignConfig
            "com.quantum.kis.client" // KisFeignClient
        })
public class KisApiAdapterConfig {
    // ComponentScan으로 자동 Bean 등록
}
