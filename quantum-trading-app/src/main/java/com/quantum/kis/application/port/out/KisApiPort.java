package com.quantum.kis.application.port.out;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.AccessTokenResponse;
import com.quantum.kis.dto.WebSocketKeyResponse;

/**
 * KIS API 호출 포트
 * 외부 KIS API와의 통신을 추상화
 */
public interface KisApiPort {

    /**
     * 액세스 토큰을 발급한다.
     * @param environment KIS 환경
     * @return 액세스 토큰 응답
     */
    AccessTokenResponse issueAccessToken(KisEnvironment environment);

    /**
     * 웹소켓 키를 발급한다.
     * @param environment KIS 환경
     * @return 웹소켓 키 응답
     */
    WebSocketKeyResponse issueWebSocketKey(KisEnvironment environment);
}