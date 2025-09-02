package com.quantum.kis.infrastructure.repository

import com.quantum.kis.domain.KisAccount
import com.quantum.kis.domain.KisEnvironment
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.util.*

/**
 * KIS 계정 레포지토리
 * 
 * 하이브리드 토큰 아키텍처에서 사용자별 KIS 계정 정보 관리
 */
@Repository
interface KisAccountRepository : JpaRepository<KisAccount, Long> {
    
    /**
     * 사용자별 활성 계정 조회
     */
    fun findByUserIdAndIsActiveTrue(userId: Long): List<KisAccount>
    
    /**
     * 사용자가 활성 계정을 가지고 있는지 확인
     */
    fun existsByUserIdAndIsActiveTrue(userId: Long): Boolean
    
    /**
     * 사용자별 환경별 활성 계정 조회
     */
    fun findByUserIdAndEnvironmentAndIsActiveTrue(
        userId: Long, 
        environment: KisEnvironment
    ): List<KisAccount>
    
    /**
     * 사용자별 환경별 첫 번째 활성 계정 조회
     */
    fun findFirstByUserIdAndEnvironmentAndIsActiveTrueOrderByCreatedAtAsc(
        userId: Long,
        environment: KisEnvironment
    ): Optional<KisAccount>
    
    /**
     * 특정 사용자의 특정 환경에서 특정 계좌번호로 계정 조회
     */
    fun findByUserIdAndEnvironmentAndAccountNumberAndIsActiveTrue(
        userId: Long,
        environment: KisEnvironment,
        accountNumber: String
    ): Optional<KisAccount>
    
    /**
     * App Key로 활성 계정 조회
     */
    fun findByAppKeyAndIsActiveTrue(appKey: String): Optional<KisAccount>
    
    /**
     * 중복 계정 확인 (같은 사용자, 환경, App Key)
     */
    fun existsByUserIdAndEnvironmentAndAppKeyAndIsActiveTrue(
        userId: Long,
        environment: KisEnvironment,
        appKey: String
    ): Boolean
    
    /**
     * 중복 계좌 확인 (같은 사용자, 환경, 계좌번호)
     */
    fun existsByUserIdAndEnvironmentAndAccountNumberAndIsActiveTrue(
        userId: Long,
        environment: KisEnvironment,
        accountNumber: String
    ): Boolean
    
    /**
     * 사용자별 환경별 계정 수 조회
     */
    fun countByUserIdAndEnvironmentAndIsActiveTrue(
        userId: Long,
        environment: KisEnvironment
    ): Long
    
    /**
     * 토큰 발급이 가능한 계정 조회 (마지막 발급으로부터 일정 시간 경과)
     */
    @Query("""
        SELECT a FROM KisAccount a 
        WHERE a.userId = :userId 
        AND a.environment = :environment 
        AND a.isActive = true
        AND (a.lastTokenIssuedAt IS NULL OR a.lastTokenIssuedAt < :minIssueTime)
        ORDER BY a.lastTokenIssuedAt ASC NULLS FIRST
    """)
    fun findAvailableForTokenIssue(
        @Param("userId") userId: Long,
        @Param("environment") environment: KisEnvironment,
        @Param("minIssueTime") minIssueTime: java.time.LocalDateTime
    ): List<KisAccount>
    
    /**
     * 최근 검증된 활성 계정 조회 (검증 시간 순)
     */
    @Query("""
        SELECT a FROM KisAccount a 
        WHERE a.userId = :userId 
        AND a.environment = :environment 
        AND a.isActive = true
        AND a.lastValidatedAt IS NOT NULL
        ORDER BY a.lastValidatedAt DESC
    """)
    fun findRecentlyValidatedAccounts(
        @Param("userId") userId: Long,
        @Param("environment") environment: KisEnvironment
    ): List<KisAccount>
    
    /**
     * 검증이 필요한 계정 조회 (검증한지 오래되었거나 미검증)
     */
    @Query("""
        SELECT a FROM KisAccount a 
        WHERE a.userId = :userId 
        AND a.isActive = true
        AND (a.lastValidatedAt IS NULL OR a.lastValidatedAt < :maxValidTime)
        ORDER BY a.lastValidatedAt ASC NULLS FIRST
    """)
    fun findAccountsNeedingValidation(
        @Param("userId") userId: Long,
        @Param("maxValidTime") maxValidTime: java.time.LocalDateTime
    ): List<KisAccount>
    
    /**
     * 사용자별 환경별 계정 별칭 중복 확인
     */
    fun existsByUserIdAndEnvironmentAndAccountAliasAndIsActiveTrue(
        userId: Long,
        environment: KisEnvironment,
        accountAlias: String
    ): Boolean
    
    /**
     * 계정 별칭으로 검색
     */
    fun findByUserIdAndAccountAliasContainingAndIsActiveTrue(
        userId: Long,
        accountAlias: String
    ): List<KisAccount>
}