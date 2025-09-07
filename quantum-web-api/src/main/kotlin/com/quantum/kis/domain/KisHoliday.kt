package com.quantum.kis.domain

import jakarta.persistence.*
import java.time.LocalDate
import java.time.LocalDateTime

/**
 * KIS API 국내 휴장일 정보 엔티티
 */
@Entity
@Table(name = "kis_domestic_holidays")
class KisHoliday(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,

    // ========== 기본 식별 정보 (테이블 앞부분) ==========
    @Column(name = "holiday_date", nullable = false, unique = true)
    val holidayDate: LocalDate = LocalDate.now(),

    @Column(name = "holiday_name")
    val holidayName: String? = null,    // 휴일명

    // ========== 상태 정보 ==========
    @Column(name = "business_day_yn", length = 1)
    val businessDayYn: String? = null,  // 영업일여부 (Y/N)

    @Column(name = "trade_day_yn", length = 1) 
    val tradeDayYn: String? = null,     // 거래일여부 (Y/N)

    @Column(name = "opening_day_yn", length = 1)
    val openingDayYn: String? = null,   // 개장일여부 (Y/N) - 주문 가능 여부 확인용

    @Column(name = "settlement_day_yn", length = 1)
    val settlementDayYn: String? = null, // 결제일여부 (Y/N)

    // ========== 시간 정보 (테이블 끝부분) ==========
    @Column(name = "created_at", nullable = false, updatable = false)
    val createdAt: LocalDateTime = LocalDateTime.now(),

    @Column(name = "updated_at", nullable = false)
    var updatedAt: LocalDateTime = LocalDateTime.now()
) {
    /**
     * 거래 가능 여부 확인
     */
    fun isTradingDay(): Boolean = openingDayYn == "Y"

    /**
     * 영업일 여부 확인  
     */
    fun isBusinessDay(): Boolean = businessDayYn == "Y"

    /**
     * 휴장일 여부 확인
     */
    fun isHoliday(): Boolean = openingDayYn != "Y"

    @PreUpdate
    fun onPreUpdate() {
        updatedAt = LocalDateTime.now()
    }
}