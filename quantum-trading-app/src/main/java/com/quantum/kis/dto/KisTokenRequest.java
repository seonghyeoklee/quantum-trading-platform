package com.quantum.kis.dto;

import com.quantum.kis.infrastructure.config.KisConfig;
import com.quantum.kis.domain.KisEnvironment;

/**
 * KIS OAuth 접근 토큰 발급 요청
 */
public record KisTokenRequest(
        String grant_type,
        String appkey,
        String appsecret
) {
    /**
     * 환경별 토큰 요청 객체를 생성한다.
     * @param env KIS 환경
     * @param config KIS 설정
     * @return 토큰 요청 객체
     */
    public static KisTokenRequest of(KisEnvironment env, KisConfig config) {
        return new KisTokenRequest(
                "client_credentials",
                config.getAppKey(env),
                config.getSecretKey(env)
        );
    }
}