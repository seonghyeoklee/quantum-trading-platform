package com.quantum.kis.infrastructure.repository

import com.quantum.kis.domain.KisEnvironment
import com.quantum.kis.domain.KisSettingPurpose
import com.quantum.kis.domain.UserKisSettings
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.util.*

/**
 * KIS 사용자 설정 레포지토리
 */
@Repository
interface UserKisSettingsRepository : JpaRepository<UserKisSettings, Long> {
    
    /**
     * 사용자별 활성화된 KIS 설정 목록 조회
     */
    fun findByUserIdAndIsActiveTrue(userId: Long): List<UserKisSettings>
    
    /**
     * 사용자별 환경별 활성화된 KIS 설정 목록 조회
     */
    fun findByUserIdAndEnvironmentAndIsActiveTrue(
        userId: Long, 
        environment: KisEnvironment
    ): List<UserKisSettings>
    
    /**
     * 사용자별 환경별 목적별 활성화된 KIS 설정 조회
     */
    fun findByUserIdAndEnvironmentAndPurposeAndIsActiveTrue(
        userId: Long,
        environment: KisEnvironment,
        purpose: KisSettingPurpose
    ): List<UserKisSettings>
    
    /**
     * 특정 계좌번호로 설정 조회
     */
    fun findByUserIdAndAccountNumberAndIsActiveTrue(
        userId: Long,
        accountNumber: String
    ): Optional<UserKisSettings>
    
    /**
     * 앱키로 설정 조회
     */
    fun findByAppKeyAndIsActiveTrue(appKey: String): Optional<UserKisSettings>
    
    /**
     * 사용자별 환경별 기본 거래 설정 조회
     */
    @Query("""
        SELECT s FROM UserKisSettings s 
        WHERE s.userId = :userId 
        AND s.environment = :environment 
        AND s.purpose = 'PRIMARY_TRADING'
        AND s.isActive = true
        ORDER BY s.createdAt ASC
    """)
    fun findPrimaryTradingSetting(
        @Param("userId") userId: Long,
        @Param("environment") environment: KisEnvironment
    ): Optional<UserKisSettings>
    
    /**
     * 사용자별 환경별 유량 확장용 설정 목록 조회
     */
    @Query("""
        SELECT s FROM UserKisSettings s 
        WHERE s.userId = :userId 
        AND s.environment = :environment 
        AND s.purpose = 'RATE_LIMIT_EXPANSION'
        AND s.isActive = true
        ORDER BY s.createdAt ASC
    """)
    fun findRateLimitExpansionSettings(
        @Param("userId") userId: Long,
        @Param("environment") environment: KisEnvironment
    ): List<UserKisSettings>
    
    /**
     * 유량이 가장 적은 활성 설정 조회 (로드 밸런싱용)
     * 실제 구현은 서비스에서 현재 사용량과 함께 계산 필요
     */
    @Query("""
        SELECT s FROM UserKisSettings s 
        WHERE s.userId = :userId 
        AND s.environment = :environment 
        AND s.isActive = true
        ORDER BY s.id ASC
    """)
    fun findAvailableSettingsForLoadBalancing(
        @Param("userId") userId: Long,
        @Param("environment") environment: KisEnvironment
    ): List<UserKisSettings>
    
    /**
     * 중복 계좌 확인 (같은 사용자, 환경, 계좌번호)
     */
    fun existsByUserIdAndEnvironmentAndAccountNumber(
        userId: Long,
        environment: KisEnvironment,
        accountNumber: String
    ): Boolean
    
    /**
     * 중복 앱키 확인
     */
    fun existsByAppKeyAndIsActiveTrue(appKey: String): Boolean
}