package com.quantum.kis.domain;

import com.quantum.kis.infrastructure.config.KisConfig;
import com.quantum.kis.dto.*;

/**
 * KIS API 토큰 타입
 * - ACCESS_TOKEN: OAuth 접근 토큰
 * - WEBSOCKET_KEY: 웹소켓 접속키
 */
public enum TokenType {
    ACCESS_TOKEN("/oauth2/tokenP") {
        @Override
        public Object createRequest(KisEnvironment env, KisConfig config) {
            return KisTokenRequest.of(env, config);
        }

        @Override
        public Class<?> getResponseType() {
            return AccessTokenResponse.class;
        }
    },

    WEBSOCKET_KEY("/oauth2/Approval") {
        @Override
        public Object createRequest(KisEnvironment env, KisConfig config) {
            return KisWebSocketRequest.of(env, config);
        }

        @Override
        public Class<?> getResponseType() {
            return WebSocketKeyResponse.class;
        }
    };

    private final String endpoint;

    TokenType(String endpoint) {
        this.endpoint = endpoint;
    }

    public String getEndpoint() {
        return endpoint;
    }

    /**
     * 토큰 타입별로 요청 객체를 생성한다.
     * @param env KIS 환경
     * @param config KIS 설정
     * @return 요청 객체
     */
    public abstract Object createRequest(KisEnvironment env, KisConfig config);

    /**
     * 토큰 타입별로 응답 타입을 반환한다.
     * @return 응답 타입 클래스
     */
    public abstract Class<?> getResponseType();
}