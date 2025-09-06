package com.quantum.kis.infrastructure.repository

import com.quantum.kis.domain.KisHoliday
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.time.LocalDate

/**
 * KIS 휴장일 정보 레포지토리 (달력용)
 */
@Repository
interface KisHolidayRepository : JpaRepository<KisHoliday, Long> {
    
    /**
     * 특정 기간의 휴장일만 조회 (달력용)
     */
    @Query("SELECT h FROM KisHoliday h WHERE h.holidayDate BETWEEN :startDate AND :endDate AND h.openingDayYn = 'N' ORDER BY h.holidayDate")
    fun findHolidaysBetween(
        @Param("startDate") startDate: LocalDate,
        @Param("endDate") endDate: LocalDate
    ): List<KisHoliday>
}