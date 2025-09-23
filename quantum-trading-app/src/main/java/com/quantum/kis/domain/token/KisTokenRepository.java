package com.quantum.kis.domain.token;

import java.util.List;
import java.util.Optional;

/**
 * KIS 토큰 리포지토리 인터페이스 (도메인 계층)
 * DDD의 Repository 패턴 구현
 */
public interface KisTokenRepository {

    /**
     * 토큰 ID로 토큰 조회
     * @param tokenId 토큰 ID
     * @return 토큰 (없으면 Optional.empty())
     */
    Optional<KisToken> findById(KisTokenId tokenId);

    /**
     * 모든 토큰 조회
     * @return 모든 토큰 리스트
     */
    List<KisToken> findAll();

    /**
     * 활성 상태의 토큰들만 조회
     * @return 활성 토큰 리스트
     */
    List<KisToken> findAllActive();

    /**
     * 만료된 토큰들 조회
     * @return 만료된 토큰 리스트
     */
    List<KisToken> findAllExpired();

    /**
     * 갱신이 필요한 토큰들 조회 (만료되었거나 곧 만료될 토큰)
     * @return 갱신 필요 토큰 리스트
     */
    List<KisToken> findTokensNeedingRenewal();

    /**
     * 토큰 저장 (생성 또는 수정)
     * @param token 저장할 토큰
     * @return 저장된 토큰
     */
    KisToken save(KisToken token);

    /**
     * 토큰 삭제
     * @param tokenId 삭제할 토큰 ID
     */
    void deleteById(KisTokenId tokenId);

    /**
     * 만료된 토큰들 일괄 삭제
     * @return 삭제된 토큰 수
     */
    int deleteExpiredTokens();

    /**
     * 토큰 존재 여부 확인
     * @param tokenId 토큰 ID
     * @return 존재하면 true
     */
    boolean existsById(KisTokenId tokenId);

    /**
     * 모든 토큰 삭제
     */
    void deleteAll();
}