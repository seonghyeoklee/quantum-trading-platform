package com.quantum.kis.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * KIS WebSocket 설정
 *
 * <p>공식 정책: - 1세션당 실시간 데이터 41건까지 등록 가능 - 국내주식/해외주식/국내파생/해외파생 모든 상품 실시간 합산 41건 - 계좌(앱키) 단위로 유량 제한
 * (1개의 계좌(앱키)당 1세션) - 1개의 PC에서 여러 개의 계좌(앱키)로 세션 연결 가능
 */
@Getter
@Setter
@Configuration
@ConfigurationProperties(prefix = "kis.websocket")
public class KisWebSocketConfig {

    /** WebSocket 서버 URL */
    private String url = "ws://ops.koreainvestment.com:21000"; // 모의투자 기본값

    /** 세션당 최대 구독 가능한 실시간 데이터 수 */
    private int maxSubscriptionsPerSession = 41;

    /** 연결 타임아웃 (밀리초) */
    private long connectionTimeoutMs = 10000;

    /** 읽기 타임아웃 (밀리초) */
    private long readTimeoutMs = 30000;

    /** 핑 간격 (밀리초) */
    private long pingIntervalMs = 30000;

    /** 재연결 시도 횟수 */
    private int maxReconnectAttempts = 5;

    /** 재연결 대기 시간 (밀리초) */
    private long reconnectDelayMs = 5000;

    /** 구독 가능한 실시간 데이터 타입들 */
    public enum SubscriptionType {
        /** 실시간 체결가 */
        REAL_TIME_PRICE("H0STCNT0"),

        /** 실시간 호가 */
        REAL_TIME_QUOTE("H0STASP0"),

        /** 실시간 예상체결 */
        EXPECTED_CONCLUSION("H0STCNI0"),

        /** 체결통보 */
        EXECUTION_NOTICE("H0STCNI9");

        private final String code;

        SubscriptionType(String code) {
            this.code = code;
        }

        public String getCode() {
            return code;
        }
    }

    /** 환경별 WebSocket URL 설정 */
    public void configureForEnvironment(String environment) {
        if ("production".equalsIgnoreCase(environment)) {
            // 실전투자 WebSocket URL
            this.url = "ws://ops.koreainvestment.com:21000";
        } else {
            // 모의투자 WebSocket URL
            this.url = "ws://ops.koreainvestment.com:31000";
        }
    }

    /** 구독 제한 체크 */
    public boolean canSubscribe(int currentSubscriptions) {
        return currentSubscriptions < maxSubscriptionsPerSession;
    }

    /** 구독 가능한 남은 슬롯 수 */
    public int getAvailableSlots(int currentSubscriptions) {
        return Math.max(0, maxSubscriptionsPerSession - currentSubscriptions);
    }
}
