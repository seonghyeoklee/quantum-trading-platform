package com.quantum.shared;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

/**
 * 시장 데이터 전송을 위한 공통 DTO
 * 모듈 간 의존성을 제거하기 위한 중립적인 데이터 구조
 */
public class MarketDataDto {

    /**
     * 차트 데이터 응답
     */
    public record ChartResponse(
            boolean success,
            String message,
            StockInfo stockInfo,
            List<DailyPrice> dailyPrices
    ) {}

    /**
     * 종목 정보
     */
    public record StockInfo(
            String stockCode,
            String stockName
    ) {}

    /**
     * 일별 가격 정보
     */
    public record DailyPrice(
            String date,         // YYYYMMDD
            String openPrice,
            String highPrice,
            String lowPrice,
            String closePrice,
            String volume
    ) {}
}