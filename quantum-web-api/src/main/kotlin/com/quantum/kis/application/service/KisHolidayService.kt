package com.quantum.kis.application.service

import com.quantum.kis.domain.KisHoliday
import com.quantum.kis.infrastructure.repository.KisHolidayRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.time.LocalDate

/**
 * KIS 휴장일 정보 서비스 (달력용)
 */
@Service
@Transactional
class KisHolidayService(
    private val holidayRepository: KisHolidayRepository
) {
    /**
     * 날짜 범위의 휴장일 목록 조회 (달력용)
     */
    @Transactional(readOnly = true)
    fun findHolidays(startDate: LocalDate, endDate: LocalDate): List<KisHoliday> {
        return holidayRepository.findHolidaysBetween(startDate, endDate)
    }
}