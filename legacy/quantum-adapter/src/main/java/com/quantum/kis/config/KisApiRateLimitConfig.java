package com.quantum.kis.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * KIS API Rate Limiting 정책 설정
 *
 * <p>공식 정책: - 실전투자: 1초당 20건 (계좌별) - 모의투자: 1초당 2건 (계좌별) - 토큰발급: 1초당 1건 - WebSocket: 1세션당 실시간 데이터 41건
 */
@Getter
@Setter
@Configuration
@ConfigurationProperties(prefix = "kis.api.rate-limit")
public class KisApiRateLimitConfig {

    /** 환경별 REST API 호출 제한 (초당) */
    private int restCallsPerSecond = 2; // 기본값: 모의투자 기준

    /** 토큰 발급 API 호출 제한 (초당) */
    private int tokenCallsPerSecond = 1;

    /** 분당 호출 제한 (안전 마진 적용) */
    private int callsPerMinute = 100; // 기본값: 2건/초 * 60초 - 20% 마진

    /** 시간당 호출 제한 (일일 제한 대비) */
    private int callsPerHour = 5000; // 기본값: 보수적 추정

    /** WebSocket 세션당 실시간 데이터 등록 제한 */
    private int websocketMaxSubscriptions = 41;

    /** Rate Limit 초과시 대기 시간 (밀리초) */
    private long waitTimeOnLimitMs = 100;

    /** Rate Limit 재시도 횟수 */
    private int maxRetryAttempts = 3;

    /** 통계 데이터 보관 기간 (시간) */
    private int statisticsRetentionHours = 24;

    /** 환경에 따른 동적 설정 */
    public void configureForEnvironment(String environment) {
        if ("production".equalsIgnoreCase(environment)) {
            // 실전투자 설정
            this.restCallsPerSecond = 20;
            this.callsPerMinute = 1000; // 20건/초 * 60초 - 20% 마진
            this.callsPerHour = 50000;
        } else {
            // 모의투자 설정 (sandbox, development)
            this.restCallsPerSecond = 2;
            this.callsPerMinute = 100; // 2건/초 * 60초 - 20% 마진
            this.callsPerHour = 5000;
        }
    }

    /** 보수적 설정 (안전 마진 추가 적용) */
    public void enableConservativeMode() {
        this.restCallsPerSecond = Math.max(1, this.restCallsPerSecond / 2);
        this.callsPerMinute = Math.max(10, this.callsPerMinute / 2);
        this.callsPerHour = Math.max(100, this.callsPerHour / 2);
        this.waitTimeOnLimitMs = Math.min(1000, this.waitTimeOnLimitMs * 2);
    }
}
