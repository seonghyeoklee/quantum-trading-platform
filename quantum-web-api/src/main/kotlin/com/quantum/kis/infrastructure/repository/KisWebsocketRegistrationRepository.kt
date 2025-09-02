package com.quantum.kis.infrastructure.repository

import com.quantum.kis.domain.KisWebsocketRegistration
import com.quantum.kis.domain.WebsocketDataType
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.util.*

/**
 * KIS 웹소켓 실시간 데이터 등록 레포지토리
 */
@Repository
interface KisWebsocketRegistrationRepository : JpaRepository<KisWebsocketRegistration, Long> {
    
    /**
     * KIS 설정별 활성화된 등록 목록 조회
     */
    fun findByKisSettingIdAndIsActiveTrueOrderByRegisteredAtAsc(
        kisSettingId: Long
    ): List<KisWebsocketRegistration>
    
    /**
     * KIS 설정별 활성화된 등록 수 계산 (41개 제한 확인용)
     */
    fun countByKisSettingIdAndIsActiveTrue(kisSettingId: Long): Long
    
    /**
     * 데이터 유형별 활성화된 등록 목록 조회
     */
    fun findByKisSettingIdAndDataTypeAndIsActiveTrueOrderByRegisteredAtAsc(
        kisSettingId: Long,
        dataType: WebsocketDataType
    ): List<KisWebsocketRegistration>
    
    /**
     * 특정 종목의 특정 데이터 유형 등록 확인
     */
    fun findByKisSettingIdAndDataTypeAndSymbolAndIsActiveTrue(
        kisSettingId: Long,
        dataType: WebsocketDataType,
        symbol: String
    ): Optional<KisWebsocketRegistration>
    
    /**
     * HTS ID를 사용한 체결통보 등록 확인
     */
    fun findByKisSettingIdAndDataTypeAndHtsIdAndIsActiveTrue(
        kisSettingId: Long,
        dataType: WebsocketDataType,
        htsId: String
    ): Optional<KisWebsocketRegistration>
    
    /**
     * 특정 종목의 모든 활성화된 등록 조회
     */
    fun findByKisSettingIdAndSymbolAndIsActiveTrueOrderByDataTypeAsc(
        kisSettingId: Long,
        symbol: String
    ): List<KisWebsocketRegistration>
    
    /**
     * 데이터 유형별 등록 수 통계
     */
    @Query("""
        SELECT r.dataType, COUNT(r) 
        FROM KisWebsocketRegistration r 
        WHERE r.kisSettingId = :kisSettingId 
        AND r.isActive = true
        GROUP BY r.dataType
    """)
    fun countByDataType(
        @Param("kisSettingId") kisSettingId: Long
    ): List<Array<Any>>
    
    /**
     * 등록 가능 여부 확인 (41개 제한)
     */
    @Query("""
        SELECT CASE WHEN COUNT(r) < 41 THEN true ELSE false END
        FROM KisWebsocketRegistration r 
        WHERE r.kisSettingId = :kisSettingId 
        AND r.isActive = true
    """)
    fun canRegisterMore(
        @Param("kisSettingId") kisSettingId: Long
    ): Boolean
    
    /**
     * 등록 가능한 슬롯 수 계산
     */
    @Query("""
        SELECT (41 - COUNT(r))
        FROM KisWebsocketRegistration r 
        WHERE r.kisSettingId = :kisSettingId 
        AND r.isActive = true
    """)
    fun getAvailableSlots(
        @Param("kisSettingId") kisSettingId: Long
    ): Long
    
    /**
     * 중복 등록 확인 - 종목 기반
     */
    fun existsByKisSettingIdAndDataTypeAndSymbolAndIsActiveTrue(
        kisSettingId: Long,
        dataType: WebsocketDataType,
        symbol: String
    ): Boolean
    
    /**
     * 중복 등록 확인 - HTS ID 기반 (체결통보)
     */
    fun existsByKisSettingIdAndDataTypeAndHtsIdAndIsActiveTrue(
        kisSettingId: Long,
        dataType: WebsocketDataType,
        htsId: String
    ): Boolean
    
    /**
     * 특정 데이터 유형의 모든 등록 해제
     */
    @Query("""
        UPDATE KisWebsocketRegistration r 
        SET r.isActive = false, r.unregisteredAt = CURRENT_TIMESTAMP
        WHERE r.kisSettingId = :kisSettingId 
        AND r.dataType = :dataType 
        AND r.isActive = true
    """)
    fun unregisterAllByDataType(
        @Param("kisSettingId") kisSettingId: Long,
        @Param("dataType") dataType: WebsocketDataType
    ): Int
    
    /**
     * 특정 종목의 모든 등록 해제
     */
    @Query("""
        UPDATE KisWebsocketRegistration r 
        SET r.isActive = false, r.unregisteredAt = CURRENT_TIMESTAMP
        WHERE r.kisSettingId = :kisSettingId 
        AND r.symbol = :symbol 
        AND r.isActive = true
    """)
    fun unregisterAllBySymbol(
        @Param("kisSettingId") kisSettingId: Long,
        @Param("symbol") symbol: String
    ): Int
    
    /**
     * KIS 설정의 모든 등록 해제
     */
    @Query("""
        UPDATE KisWebsocketRegistration r 
        SET r.isActive = false, r.unregisteredAt = CURRENT_TIMESTAMP
        WHERE r.kisSettingId = :kisSettingId 
        AND r.isActive = true
    """)
    fun unregisterAllBySetting(
        @Param("kisSettingId") kisSettingId: Long
    ): Int
}