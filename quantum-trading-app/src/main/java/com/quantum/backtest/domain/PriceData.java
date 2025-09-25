package com.quantum.backtest.domain;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Objects;

/**
 * 주가 데이터 Value Object
 * OHLCV 데이터를 표현
 */
public record PriceData(
        LocalDate date,         // 일자
        BigDecimal open,        // 시가
        BigDecimal high,        // 고가
        BigDecimal low,         // 저가
        BigDecimal close,       // 종가
        long volume             // 거래량
) {

    public PriceData {
        Objects.requireNonNull(date, "Date cannot be null");
        Objects.requireNonNull(open, "Open price cannot be null");
        Objects.requireNonNull(high, "High price cannot be null");
        Objects.requireNonNull(low, "Low price cannot be null");
        Objects.requireNonNull(close, "Close price cannot be null");

        if (open.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Open price must be positive");
        }
        if (high.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("High price must be positive");
        }
        if (low.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Low price must be positive");
        }
        if (close.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Close price must be positive");
        }
        if (volume < 0) {
            throw new IllegalArgumentException("Volume cannot be negative");
        }

        // OHLC 논리적 검증
        if (high.compareTo(open) < 0 || high.compareTo(close) < 0 ||
            high.compareTo(low) < 0 || low.compareTo(open) > 0 ||
            low.compareTo(close) > 0) {
            throw new IllegalArgumentException("Invalid OHLC relationship: H=" + high +
                ", L=" + low + ", O=" + open + ", C=" + close);
        }
    }

    /**
     * 일일 변동률 계산 (종가 기준)
     */
    public BigDecimal getDailyChangeRate() {
        if (open.compareTo(BigDecimal.ZERO) == 0) {
            return BigDecimal.ZERO;
        }
        return close.subtract(open).divide(open, 4, java.math.RoundingMode.HALF_UP);
    }

    /**
     * 일일 변동폭 계산
     */
    public BigDecimal getDailyRange() {
        return high.subtract(low);
    }

    /**
     * 일일 변동률 (%) 계산
     */
    public BigDecimal getDailyChangePercent() {
        return getDailyChangeRate().multiply(BigDecimal.valueOf(100));
    }

    /**
     * 상승장인지 확인
     */
    public boolean isBullish() {
        return close.compareTo(open) > 0;
    }

    /**
     * 하락장인지 확인
     */
    public boolean isBearish() {
        return close.compareTo(open) < 0;
    }

    /**
     * 보합인지 확인
     */
    public boolean isFlat() {
        return close.compareTo(open) == 0;
    }
}