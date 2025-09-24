package com.quantum.kis.application.port.in;

import com.quantum.kis.domain.KisEnvironment;

/**
 * 토큰 조회 Use Case
 */
public interface GetTokenUseCase {

    /**
     * 유효한 액세스 토큰을 반환한다. 만료된 경우 자동으로 재발급한다.
     * @param environment KIS 환경
     * @return 액세스 토큰
     */
    String getValidAccessToken(KisEnvironment environment);

    /**
     * 유효한 웹소켓 키를 반환한다. 만료된 경우 자동으로 재발급한다.
     * @param environment KIS 환경
     * @return 웹소켓 키
     */
    String getValidWebSocketKey(KisEnvironment environment);
}