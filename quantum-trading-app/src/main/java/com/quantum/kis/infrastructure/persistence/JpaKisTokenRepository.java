package com.quantum.kis.infrastructure.persistence;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import com.quantum.kis.domain.token.TokenStatus;

import java.time.LocalDateTime;
import java.util.List;

/**
 * KisTokenEntity용 Spring Data JPA 리포지토리
 */
@Repository
public interface JpaKisTokenRepository extends JpaRepository<KisTokenEntity, String> {

    /**
     * 활성 상태의 토큰들 조회
     */
    List<KisTokenEntity> findByStatus(TokenStatus status);

    /**
     * 만료된 토큰들 조회 (만료 시간이 현재 시간보다 이전)
     */
    @Query("SELECT t FROM KisTokenEntity t WHERE t.expiresAt < :now")
    List<KisTokenEntity> findExpiredTokens(LocalDateTime now);

    /**
     * 갱신이 필요한 토큰들 조회
     * - 만료된 토큰
     * - 1시간 내에 만료될 토큰
     * - 무효한 상태의 토큰
     */
    @Query("SELECT t FROM KisTokenEntity t WHERE " +
           "t.expiresAt < :expiringSoon OR " +
           "t.status = :invalidStatus OR " +
           "t.status = :expiredStatus")
    List<KisTokenEntity> findTokensNeedingRenewal(
            LocalDateTime expiringSoon,
            TokenStatus invalidStatus,
            TokenStatus expiredStatus
    );

    /**
     * 만료된 토큰들 일괄 삭제
     */
    @Modifying
    @Query("DELETE FROM KisTokenEntity t WHERE t.expiresAt < :now OR t.status = :expiredStatus")
    int deleteExpiredTokens(LocalDateTime now, TokenStatus expiredStatus);

    /**
     * 특정 상태의 토큰 개수 조회
     */
    long countByStatus(TokenStatus status);

    /**
     * 마지막 업데이트 시간 기준으로 토큰 조회 (최신순)
     */
    List<KisTokenEntity> findAllByOrderByLastUpdatedAtDesc();
}