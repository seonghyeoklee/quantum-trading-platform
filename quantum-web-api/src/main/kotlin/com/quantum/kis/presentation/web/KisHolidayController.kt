package com.quantum.kis.presentation.web

import com.quantum.kis.application.service.KisHolidayService
import com.quantum.kis.presentation.dto.HolidayCalendarItem
import com.quantum.kis.presentation.dto.HolidayCalendarResponse
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.Parameter
import io.swagger.v3.oas.annotations.media.Content
import io.swagger.v3.oas.annotations.media.Schema
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.tags.Tag
import org.slf4j.LoggerFactory
import org.springframework.format.annotation.DateTimeFormat
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import java.time.LocalDate

/**
 * KIS 휴장일 정보 컨트롤러 (달력용)
 * 
 * 한국투자증권 API에서 제공하는 영업일/거래일/개장일/결제일 정보를 달력 형태로 제공합니다.
 */
@RestController
@RequestMapping("/api/v1/kis/holidays")
@Tag(name = "KIS Holiday Calendar", description = "KIS 휴장일 및 영업일 달력 정보 API")
@CrossOrigin(origins = ["*"])
class KisHolidayController(
    private val kisHolidayService: KisHolidayService
) {
    private val logger = LoggerFactory.getLogger(KisHolidayController::class.java)

    /**
     * 달력용 휴장일 정보 조회
     */
    @GetMapping("/calendar")
    @Operation(
        summary = "KIS 휴장일 달력 정보 조회",
        description = "지정된 기간의 영업일/거래일/개장일/결제일 정보를 달력 형태로 조회합니다. " +
                "한국투자증권 API에서 제공하는 공식 휴장일 정보를 기반으로 합니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200",
            description = "달력 정보 조회 성공",
            content = [Content(
                schema = Schema(implementation = HolidayCalendarResponse::class)
            )]
        ),
        ApiResponse(
            responseCode = "400",
            description = "잘못된 날짜 범위 (시작일이 종료일보다 늦음)"
        ),
        ApiResponse(
            responseCode = "500",
            description = "서버 오류로 인한 조회 실패"
        )
    )
    fun getCalendarInfo(
        @Parameter(
            description = "조회 시작일 (ISO 날짜 형식: YYYY-MM-DD)",
            example = "2024-01-01",
            required = true
        )
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) startDate: LocalDate,
        
        @Parameter(
            description = "조회 종료일 (ISO 날짜 형식: YYYY-MM-DD)",
            example = "2024-01-31",
            required = true
        )
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) endDate: LocalDate
    ): ResponseEntity<HolidayCalendarResponse> {
        return try {
            // 입력 검증
            if (startDate.isAfter(endDate)) {
                return ResponseEntity.badRequest().build()
            }
            
            // 휴장일 정보 조회
            val holidays = kisHolidayService.findHolidays(startDate, endDate)
            
            // 달력용 데이터 구성
            val calendarItems = holidays.map { holiday ->
                HolidayCalendarItem(
                    date = holiday.holidayDate,
                    holidayName = holiday.holidayName,
                    isBusinessDay = holiday.businessDayYn == "Y",
                    isTradingDay = holiday.tradeDayYn == "Y", 
                    isOpeningDay = holiday.openingDayYn == "Y",
                    isSettlementDay = holiday.settlementDayYn == "Y"
                )
            }
            
            val response = HolidayCalendarResponse(
                startDate = startDate,
                endDate = endDate,
                calendar = calendarItems,
                totalCount = calendarItems.size
            )
            
            ResponseEntity.ok(response)
            
        } catch (e: Exception) {
            logger.error("달력 정보 조회 실패: ${e.message}", e)
            ResponseEntity.internalServerError().build()
        }
    }
}