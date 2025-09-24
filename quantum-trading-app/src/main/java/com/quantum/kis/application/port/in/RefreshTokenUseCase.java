package com.quantum.kis.application.port.in;

import com.quantum.kis.domain.KisEnvironment;

/**
 * 토큰 재발급 Use Case
 */
public interface RefreshTokenUseCase {

    /**
     * 액세스 토큰을 강제로 재발급한다.
     * @param environment KIS 환경
     * @return 새로운 액세스 토큰
     */
    String refreshAccessToken(KisEnvironment environment);

    /**
     * 웹소켓 키를 강제로 재발급한다.
     * @param environment KIS 환경
     * @return 새로운 웹소켓 키
     */
    String refreshWebSocketKey(KisEnvironment environment);

    /**
     * 모든 환경의 모든 토큰을 재발급한다.
     */
    void refreshAllTokens();
}