package com.quantum.kis.application.port.outgoing

import com.quantum.kis.domain.KisHoliday
import java.time.LocalDate

/**
 * KIS 휴장일 관련 출력 포트 (헥사고날 아키텍처)
 */
interface KisHolidayPort {
    
    /**
     * 기간별 휴장일 조회
     */
    fun findHolidaysBetween(startDate: LocalDate, endDate: LocalDate): List<KisHoliday>
}