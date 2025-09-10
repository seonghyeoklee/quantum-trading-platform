package com.quantum.kis.infrastructure.repository

import com.quantum.kis.domain.KisEnvironment
import com.quantum.kis.domain.KisToken
import com.quantum.kis.domain.TokenStatus
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Modifying
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.time.LocalDateTime
import java.util.*

/**
 * KIS 토큰 레포지토리
 * 
 * 하이브리드 토큰 아키텍처에서 KIS 액세스 토큰 생명주기 관리
 * 헥사고날 아키텍처의 KisTokenPort를 구현하여 의존성 역전
 */
@Repository
interface KisTokenRepository : JpaRepository<KisToken, Long> {
    
    /**
     * 사용자별 환경별 활성 토큰 조회
     */
    fun findByUserIdAndEnvironmentAndStatus(
        userId: Long,
        environment: KisEnvironment,
        status: TokenStatus
    ): List<KisToken>
    
    /**
     * 사용자별 환경별 가장 최근 활성 토큰 조회
     */
    fun findFirstByUserIdAndEnvironmentAndStatusOrderByCreatedAtDesc(
        userId: Long,
        environment: KisEnvironment,
        status: TokenStatus
    ): Optional<KisToken>
    
    /**
     * KIS 계정별 활성 토큰 조회
     */
    fun findByKisAccountIdAndStatus(
        kisAccountId: Long,
        status: TokenStatus
    ): List<KisToken>
    
    /**
     * KIS 계정별 가장 최근 토큰 조회 (상태 무관)
     */
    fun findFirstByKisAccountIdOrderByCreatedAtDesc(
        kisAccountId: Long
    ): Optional<KisToken>
    
    /**
     * 만료 예정 토큰 조회 (자동 갱신 대상)
     */
    fun findByStatusAndNextRefreshAtBeforeOrderByNextRefreshAtAsc(
        status: TokenStatus,
        refreshTime: LocalDateTime
    ): List<KisToken>
    
    /**
     * 만료된 토큰 조회 (정리 대상)
     */
    fun findByStatusAndExpiresAtBefore(
        status: TokenStatus,
        expireTime: LocalDateTime
    ): List<KisToken>
    
    /**
     * 사용자별 환경별 토큰 수 조회
     */
    fun countByUserIdAndEnvironmentAndStatus(
        userId: Long,
        environment: KisEnvironment,
        status: TokenStatus
    ): Long
    
    /**
     * 특정 사용자의 모든 활성 토큰 조회
     */
    fun findByUserIdAndStatusOrderByCreatedAtDesc(
        userId: Long,
        status: TokenStatus
    ): List<KisToken>
    
    /**
     * 특정 기간 내에 생성된 토큰 조회
     */
    fun findByCreatedAtBetweenOrderByCreatedAtDesc(
        startTime: LocalDateTime,
        endTime: LocalDateTime
    ): List<KisToken>
    
    /**
     * 갱신 횟수가 많은 토큰 조회 (문제 토큰 감지)
     */
    fun findByRefreshCountGreaterThanOrderByRefreshCountDesc(
        minRefreshCount: Int
    ): List<KisToken>
    
    /**
     * 최근 사용되지 않은 토큰 조회
     */
    @Query("""
        SELECT t FROM KisToken t 
        WHERE t.status = :status 
        AND (t.lastUsedAt IS NULL OR t.lastUsedAt < :lastUsedBefore)
        ORDER BY t.lastUsedAt ASC NULLS FIRST
    """)
    fun findUnusedTokens(
        @Param("status") status: TokenStatus,
        @Param("lastUsedBefore") lastUsedBefore: LocalDateTime
    ): List<KisToken>
    
    /**
     * 특정 상태의 토큰들을 일괄 상태 변경
     */
    @Modifying
    @Query("""
        UPDATE KisToken t 
        SET t.status = :newStatus, t.updatedAt = :updateTime
        WHERE t.status = :currentStatus 
        AND t.expiresAt < :expireTime
    """)
    fun bulkUpdateExpiredTokens(
        @Param("currentStatus") currentStatus: TokenStatus,
        @Param("newStatus") newStatus: TokenStatus,
        @Param("expireTime") expireTime: LocalDateTime,
        @Param("updateTime") updateTime: LocalDateTime
    ): Int
    
    /**
     * 사용자별 환경별 기존 활성 토큰 비활성화
     */
    @Modifying
    @Query("""
        UPDATE KisToken t 
        SET t.status = :newStatus, t.updatedAt = :updateTime
        WHERE t.userId = :userId 
        AND t.environment = :environment 
        AND t.status = :currentStatus
        AND t.id != :excludeTokenId
    """)
    fun deactivateOtherTokens(
        @Param("userId") userId: Long,
        @Param("environment") environment: KisEnvironment,
        @Param("currentStatus") currentStatus: TokenStatus,
        @Param("newStatus") newStatus: TokenStatus,
        @Param("excludeTokenId") excludeTokenId: Long,
        @Param("updateTime") updateTime: LocalDateTime
    ): Int
    
    /**
     * 토큰 통계 조회 - 환경별 활성 토큰 수
     */
    @Query("""
        SELECT t.environment, COUNT(t) 
        FROM KisToken t 
        WHERE t.status = :status 
        GROUP BY t.environment
    """)
    fun countActiveTokensByEnvironment(
        @Param("status") status: TokenStatus
    ): List<Array<Any>>
    
    /**
     * 토큰 통계 조회 - 사용자별 토큰 수 (상위 N개)
     */
    @Query("""
        SELECT t.userId, COUNT(t) as tokenCount
        FROM KisToken t 
        WHERE t.status = :status 
        GROUP BY t.userId 
        ORDER BY tokenCount DESC
        LIMIT :limit
    """)
    fun findTopUsersByTokenCount(
        @Param("status") status: TokenStatus,
        @Param("limit") limit: Int
    ): List<Array<Any>>
    
    /**
     * 특정 기간 토큰 갱신 통계
     */
    @Query("""
        SELECT DATE(t.updatedAt) as refreshDate, COUNT(t) as refreshCount
        FROM KisToken t 
        WHERE t.updatedAt BETWEEN :startDate AND :endDate
        AND t.refreshCount > 0
        GROUP BY DATE(t.updatedAt)
        ORDER BY refreshDate DESC
    """)
    fun getRefreshStatistics(
        @Param("startDate") startDate: LocalDateTime,
        @Param("endDate") endDate: LocalDateTime
    ): List<Array<Any>>
    
    /**
     * 토큰 만료 임박 알림 대상 조회
     */
    @Query("""
        SELECT t FROM KisToken t 
        WHERE t.status = :status 
        AND t.expiresAt BETWEEN :now AND :alertTime
        AND t.nextRefreshAt IS NOT NULL
        ORDER BY t.expiresAt ASC
    """)
    fun findTokensNeedingAlert(
        @Param("status") status: TokenStatus,
        @Param("now") now: LocalDateTime,
        @Param("alertTime") alertTime: LocalDateTime
    ): List<KisToken>
}