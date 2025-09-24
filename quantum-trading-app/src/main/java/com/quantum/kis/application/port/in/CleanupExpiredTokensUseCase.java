package com.quantum.kis.application.port.in;

/**
 * 만료된 토큰 정리 Use Case
 */
public interface CleanupExpiredTokensUseCase {

    /**
     * 만료된 토큰들을 정리한다.
     * @return 정리된 토큰 수
     */
    int cleanupExpiredTokens();
}