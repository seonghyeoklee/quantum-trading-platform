package com.quantum.core.domain.port.repository;

import com.quantum.core.domain.model.kis.KisToken;

import java.util.Optional;

/**
 * KIS 토큰 리포지토리 인터페이스
 */
public interface KisTokenRepository {

    /**
     * 토큰 저장
     */
    KisToken save(KisToken token);

    /**
     * 활성화된 유효한 토큰 조회
     */
    Optional<KisToken> findActiveValidToken();

    /**
     * 모든 토큰 비활성화
     */
    void deactivateAllTokens();

    /**
     * 만료된 토큰 정리
     */
    void deleteExpiredTokens();
}