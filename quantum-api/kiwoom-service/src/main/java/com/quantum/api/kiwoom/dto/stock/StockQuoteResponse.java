package com.quantum.api.kiwoom.dto.stock;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 주식 현재가 조회 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StockQuoteResponse {
    private String symbol;              // 종목코드
    private String stockName;           // 종목명
    private BigDecimal currentPrice;    // 현재가
    private BigDecimal previousClose;   // 전일종가
    private BigDecimal changeAmount;    // 전일대비
    private BigDecimal changeRate;      // 등락률
    private BigDecimal openPrice;       // 시가
    private BigDecimal highPrice;       // 고가
    private BigDecimal lowPrice;        // 저가
    private Long volume;                // 거래량
    private BigDecimal tradingValue;    // 거래대금
    private BigDecimal askPrice;        // 매도호가
    private BigDecimal bidPrice;        // 매수호가
    private BigDecimal upperLimit;      // 상한가
    private BigDecimal lowerLimit;      // 하한가
    private LocalDateTime timestamp;    // 시간
}