package com.quantum.kis.application.port.out;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.token.KisToken;
import com.quantum.kis.domain.token.KisTokenId;

import java.util.List;
import java.util.Optional;

/**
 * KIS 토큰 저장소 포트
 * 도메인 레이어에서 정의한 KisTokenRepository와 유사하지만
 * Application 레이어의 요구사항에 맞춰 확장된 인터페이스
 */
public interface KisTokenRepositoryPort {

    /**
     * ID로 토큰을 조회한다.
     * @param id 토큰 ID
     * @return 토큰 (Optional)
     */
    Optional<KisToken> findById(KisTokenId id);

    /**
     * 토큰을 저장한다.
     * @param kisToken 저장할 토큰
     * @return 저장된 토큰
     */
    KisToken save(KisToken kisToken);

    /**
     * 모든 토큰을 조회한다.
     * @return 토큰 리스트
     */
    List<KisToken> findAll();

    /**
     * 특정 환경의 토큰들을 조회한다.
     * @param environment KIS 환경
     * @return 토큰 리스트
     */
    List<KisToken> findByEnvironment(KisEnvironment environment);

    /**
     * 갱신이 필요한 토큰들을 조회한다.
     * @return 갱신 필요 토큰 리스트
     */
    List<KisToken> findTokensNeedingRenewal();

    /**
     * 만료된 토큰들을 조회한다.
     * @return 만료된 토큰 리스트
     */
    List<KisToken> findAllExpired();

    /**
     * 만료된 토큰들을 데이터베이스에서 삭제한다.
     * @return 삭제된 토큰 수
     */
    int deleteExpiredTokens();
}