package com.quantum.backtest.domain;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Map;
import java.util.Objects;

/**
 * 백테스팅 설정 Value Object
 */
public record BacktestConfig(
        String stockCode,               // 종목코드 (예: "005930")
        String stockName,               // 종목명 (예: "삼성전자")
        LocalDate startDate,            // 시작일
        LocalDate endDate,              // 종료일
        BigDecimal initialCapital,      // 초기자금
        StrategyType strategyType,      // 전략 타입
        Map<String, Object> strategyParams  // 전략 파라미터
) {

    public BacktestConfig {
        Objects.requireNonNull(stockCode, "Stock code cannot be null");
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
}