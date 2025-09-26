package com.quantum.backtest.domain;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Map;
import java.util.Objects;

/**
 * 백테스팅 설정 Value Object
 */
public record BacktestConfig(
        String stockCode,               // 종목코드 (예: "005930", "AAPL")
        String stockName,               // 종목명 (예: "삼성전자", "Apple Inc.")
        MarketType marketType,          // 시장 구분 (국내/해외)
        LocalDate startDate,            // 시작일
        LocalDate endDate,              // 종료일
        BigDecimal initialCapital,      // 초기자금
        StrategyType strategyType,      // 전략 타입
        Map<String, Object> strategyParams  // 전략 파라미터
) {

    public BacktestConfig {
        Objects.requireNonNull(stockCode, "Stock code cannot be null");
        Objects.requireNonNull(marketType, "Market type cannot be null");
        Objects.requireNonNull(startDate, "Start date cannot be null");
        Objects.requireNonNull(endDate, "End date cannot be null");
        Objects.requireNonNull(initialCapital, "Initial capital cannot be null");
        Objects.requireNonNull(strategyType, "Strategy type cannot be null");
        Objects.requireNonNull(strategyParams, "Strategy params cannot be null");

        if (stockCode.isBlank()) {
            throw new IllegalArgumentException("Stock code cannot be blank");
        }
        if (startDate.isAfter(endDate)) {
            throw new IllegalArgumentException("Start date must be before end date");
        }
        if (initialCapital.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Initial capital must be positive");
        }
    }

    /**
     * 백테스팅 기간을 일수로 반환
     */
    public long getPeriodDays() {
        return startDate.datesUntil(endDate.plusDays(1)).count();
    }

    /**
     * 백테스팅 기간을 연수로 반환 (소수점)
     */
    public double getPeriodYears() {
        return getPeriodDays() / 365.0;
    }

    /**
     * 전략 파라미터를 조회
     */
    @SuppressWarnings("unchecked")
    public <T> T getStrategyParam(String key, T defaultValue) {
        return (T) strategyParams.getOrDefault(key, defaultValue);
    }

    /**
     * 종목코드를 보고 시장 구분을 자동 판별하여 BacktestConfig를 생성한다.
     */
    public static BacktestConfig createWithAutoDetection(
            String stockCode, String stockName, LocalDate startDate, LocalDate endDate,
            BigDecimal initialCapital, StrategyType strategyType, Map<String, Object> strategyParams) {

        MarketType detectedMarketType = MarketType.detectMarketType(stockCode);
        return new BacktestConfig(stockCode, stockName, detectedMarketType, startDate, endDate,
                                initialCapital, strategyType, strategyParams);
    }

    /**
     * 국내 시장인지 확인
     */
    public boolean isDomestic() {
        return marketType.isDomestic();
    }

    /**
     * 해외 시장인지 확인
     */
    public boolean isOverseas() {
        return marketType.isOverseas();
    }
}