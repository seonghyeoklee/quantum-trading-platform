package com.quantum.kis.domain;

/**
 * KIS API 토큰 타입
 * - ACCESS_TOKEN: OAuth 접근 토큰
 * - WEBSOCKET_KEY: 웹소켓 접속키
 */
public enum TokenType {
    ACCESS_TOKEN("/oauth2/tokenP"),
    WEBSOCKET_KEY("/oauth2/Approval");

    private final String endpoint;

    TokenType(String endpoint) {
        this.endpoint = endpoint;
    }

    public String getEndpoint() {
        return endpoint;
    }
}