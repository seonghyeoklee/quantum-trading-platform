package com.quantum.kis.presentation.dto

import io.swagger.v3.oas.annotations.media.Schema
import java.time.LocalDate

/**
 * 휴장일 달력 개별 항목 DTO
 */
@Schema(description = "휴장일 달력 개별 항목")
data class HolidayCalendarItem(
    @Schema(description = "날짜", example = "2024-01-01")
    val date: LocalDate,
    
    @Schema(description = "휴일명", example = "신정")
    val holidayName: String?,
    
    @Schema(description = "영업일 여부", example = "false")
    val isBusinessDay: Boolean,
    
    @Schema(description = "거래일 여부", example = "false")
    val isTradingDay: Boolean,
    
    @Schema(description = "개장일 여부", example = "false")
    val isOpeningDay: Boolean,
    
    @Schema(description = "결제일 여부", example = "false")
    val isSettlementDay: Boolean
)

/**
 * 휴장일 달력 응답 DTO
 */
@Schema(description = "휴장일 달력 응답")
data class HolidayCalendarResponse(
    @Schema(description = "조회 시작일", example = "2024-01-01")
    val startDate: LocalDate,
    
    @Schema(description = "조회 종료일", example = "2024-01-31")
    val endDate: LocalDate,
    
    @Schema(description = "달력 정보 목록")
    val calendar: List<HolidayCalendarItem>,
    
    @Schema(description = "총 개수", example = "31")
    val totalCount: Int
)