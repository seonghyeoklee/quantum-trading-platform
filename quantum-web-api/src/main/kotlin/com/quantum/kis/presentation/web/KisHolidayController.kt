package com.quantum.kis.presentation.web

import com.quantum.kis.application.service.KisHolidayService
import org.slf4j.LoggerFactory
import org.springframework.format.annotation.DateTimeFormat
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import java.time.LocalDate

/**
 * KIS 휴장일 정보 컨트롤러 (달력용)
 */
@RestController
@RequestMapping("/api/v1/kis/holidays")
@CrossOrigin(origins = ["*"])
class KisHolidayController(
    private val kisHolidayService: KisHolidayService
) {
    private val logger = LoggerFactory.getLogger(KisHolidayController::class.java)

    /**
     * 달력용 휴장일 정보 조회
     * 
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 날짜별 영업일/거래일/개장일/결제일 정보
     */
    @GetMapping("/calendar")
    fun getCalendarInfo(
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) startDate: LocalDate,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) endDate: LocalDate
    ): ResponseEntity<Map<String, Any>> {
        return try {
            // 입력 검증
            if (startDate.isAfter(endDate)) {
                return ResponseEntity.badRequest().body(mapOf(
                    "success" to false,
                    "message" to "시작 날짜가 종료 날짜보다 늦을 수 없습니다"
                ))
            }
            
            // 휴장일 정보 조회
            val holidays = kisHolidayService.findHolidays(startDate, endDate)
            
            // 달력용 데이터 구성
            val calendarData = holidays.map { holiday ->
                mapOf(
                    "date" to holiday.holidayDate,
                    "holidayName" to holiday.holidayName,
                    "isBusinessDay" to (holiday.businessDayYn == "Y"),
                    "isTradingDay" to (holiday.tradeDayYn == "Y"), 
                    "isOpeningDay" to (holiday.openingDayYn == "Y"),
                    "isSettlementDay" to (holiday.settlementDayYn == "Y")
                )
            }
            
            ResponseEntity.ok(mapOf(
                "success" to true,
                "data" to mapOf(
                    "startDate" to startDate,
                    "endDate" to endDate,
                    "calendar" to calendarData,
                    "totalCount" to calendarData.size
                ),
                "message" to "달력 정보 조회 완료"
            ))
            
        } catch (e: Exception) {
            logger.error("달력 정보 조회 실패: ${e.message}", e)
            ResponseEntity.internalServerError().body(mapOf(
                "success" to false,
                "message" to "달력 정보 조회 실패: ${e.message}"
            ))
        }
    }
}