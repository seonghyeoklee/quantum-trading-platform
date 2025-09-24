package com.quantum.kis.dto;

import com.quantum.kis.infrastructure.config.KisConfig;
import com.quantum.kis.domain.KisEnvironment;

/**
 * KIS 웹소켓 접속키 발급 요청
 * 주의: secretkey 필드명이 액세스 토큰의 appsecret과 다름
 */
public record KisWebSocketRequest(
        String grant_type,
        String appkey,
        String secretkey
) {
    /**
     * 환경별 웹소켓 키 요청 객체를 생성한다.
     * @param env KIS 환경
     * @param config KIS 설정
     * @return 웹소켓 키 요청 객체
     */
    public static KisWebSocketRequest of(KisEnvironment env, KisConfig config) {
        return new KisWebSocketRequest(
                "client_credentials",
                config.getAppKey(env),
                config.getSecretKey(env)
        );
    }
}