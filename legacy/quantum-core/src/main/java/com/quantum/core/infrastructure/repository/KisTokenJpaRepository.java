package com.quantum.core.infrastructure.repository;

import com.quantum.core.domain.model.kis.KisToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;

/**
 * KIS 토큰 JPA 리포지토리 (Spring Data JPA)
 */
public interface KisTokenJpaRepository extends JpaRepository<KisToken, Long> {

    /**
     * 활성화된 유효한 토큰 조회
     */
    @Query("""
        SELECT t FROM KisToken t 
        WHERE t.isActive = true 
        AND t.expiresAt > CURRENT_TIMESTAMP 
        ORDER BY t.createdAt DESC 
        LIMIT 1
        """)
    Optional<KisToken> findActiveValidToken();

    /**
     * 모든 토큰 비활성화
     */
    @Modifying
    @Transactional
    @Query("UPDATE KisToken t SET t.isActive = false")
    void deactivateAllTokens();

    /**
     * 만료된 토큰 정리 (3일 이전)
     */
    @Modifying
    @Transactional
    @Query("DELETE FROM KisToken t WHERE t.expiresAt < :cutoffTime")
    void deleteTokensBefore(@Param("cutoffTime") LocalDateTime cutoffTime);
}