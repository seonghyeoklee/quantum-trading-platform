package com.quantum.api.kiwoom.dto.stock;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 일봉 조회 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DailyPriceResponse {
    private LocalDate date;             // 날짜
    private BigDecimal openPrice;       // 시가
    private BigDecimal highPrice;       // 고가
    private BigDecimal lowPrice;        // 저가
    private BigDecimal closePrice;      // 종가
    private Long volume;                // 거래량
    private BigDecimal tradingValue;    // 거래대금
    private BigDecimal changeAmount;    // 전일대비
    private BigDecimal changeRate;      // 등락률
}