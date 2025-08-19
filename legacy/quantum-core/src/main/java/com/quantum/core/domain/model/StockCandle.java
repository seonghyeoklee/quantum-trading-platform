package com.quantum.core.domain.model;

import com.quantum.core.domain.model.common.TimeframeCode;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Objects;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

/** 주식 캔들(봉) 데이터 엔티티 차트 분석 및 기술적 분석을 위한 OHLCV 데이터 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
@Table(
        name = "tb_stock_candle",
        uniqueConstraints = @UniqueConstraint(columnNames = {"symbol", "timeframe", "timestamp"}),
        indexes = {
            @Index(name = "idx_candle_symbol_timeframe", columnList = "symbol, timeframe"),
            @Index(name = "idx_candle_timestamp", columnList = "timestamp"),
            @Index(name = "idx_candle_symbol_time", columnList = "symbol, timestamp")
        })
public class StockCandle {

    // Getters
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "symbol", nullable = false, length = 20)
    private String symbol;

    @Enumerated(EnumType.STRING)
    @Column(name = "timeframe", nullable = false, length = 10)
    @Comment("시간 단위: 1m, 5m, 15m, 30m, 1h, 1d, 1w, 1M")
    private TimeframeCode timeframe;

    @Column(name = "timestamp", nullable = false)
    private LocalDateTime timestamp;

    @Column(name = "open_price", nullable = false, precision = 15, scale = 2)
    private BigDecimal openPrice;

    @Column(name = "high_price", nullable = false, precision = 15, scale = 2)
    private BigDecimal highPrice;

    @Column(name = "low_price", nullable = false, precision = 15, scale = 2)
    private BigDecimal lowPrice;

    @Column(name = "close_price", nullable = false, precision = 15, scale = 2)
    private BigDecimal closePrice;

    @Column(name = "volume", nullable = false)
    private Long volume;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    private StockCandle(
            String symbol,
            TimeframeCode timeframe,
            LocalDateTime timestamp,
            BigDecimal openPrice,
            BigDecimal highPrice,
            BigDecimal lowPrice,
            BigDecimal closePrice,
            Long volume) {
        this.symbol = Objects.requireNonNull(symbol, "Symbol cannot be null");
        this.timeframe = Objects.requireNonNull(timeframe, "Timeframe cannot be null");
        this.timestamp = Objects.requireNonNull(timestamp, "Timestamp cannot be null");
        this.openPrice = Objects.requireNonNull(openPrice, "Open price cannot be null");
        this.highPrice = Objects.requireNonNull(highPrice, "High price cannot be null");
        this.lowPrice = Objects.requireNonNull(lowPrice, "Low price cannot be null");
        this.closePrice = Objects.requireNonNull(closePrice, "Close price cannot be null");
        this.volume = Objects.requireNonNull(volume, "Volume cannot be null");
        this.createdAt = LocalDateTime.now();

        validatePrices();
        validateVolume();
    }

    public static StockCandle create(
            String symbol,
            TimeframeCode timeframe,
            LocalDateTime timestamp,
            BigDecimal openPrice,
            BigDecimal highPrice,
            BigDecimal lowPrice,
            BigDecimal closePrice,
            Long volume) {
        return new StockCandle(
                symbol, timeframe, timestamp, openPrice, highPrice, lowPrice, closePrice, volume);
    }

    private void validatePrices() {
        if (openPrice.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Open price must be positive");
        }
        if (highPrice.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("High price must be positive");
        }
        if (lowPrice.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Low price must be positive");
        }
        if (closePrice.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Close price must be positive");
        }
        if (highPrice.compareTo(lowPrice) < 0) {
            throw new IllegalArgumentException("High price cannot be lower than low price");
        }
        if (openPrice.compareTo(lowPrice) < 0 || openPrice.compareTo(highPrice) > 0) {
            throw new IllegalArgumentException("Open price must be between high and low prices");
        }
        if (closePrice.compareTo(lowPrice) < 0 || closePrice.compareTo(highPrice) > 0) {
            throw new IllegalArgumentException("Close price must be between high and low prices");
        }
    }

    private void validateVolume() {
        if (volume < 0) {
            throw new IllegalArgumentException("Volume cannot be negative");
        }
    }

    /** 몸통 크기 계산 (|종가 - 시가|) */
    public BigDecimal getBodySize() {
        return closePrice.subtract(openPrice).abs();
    }

    /** 상한가 길이 계산 (고가 - max(시가, 종가)) */
    public BigDecimal getUpperShadowLength() {
        BigDecimal bodyTop = openPrice.max(closePrice);
        return highPrice.subtract(bodyTop);
    }

    /** 하한가 길이 계산 (min(시가, 종가) - 저가) */
    public BigDecimal getLowerShadowLength() {
        BigDecimal bodyBottom = openPrice.min(closePrice);
        return bodyBottom.subtract(lowPrice);
    }

    /** 양봉 여부 (종가 > 시가) */
    public boolean isBullish() {
        return closePrice.compareTo(openPrice) > 0;
    }

    /** 음봉 여부 (종가 < 시가) */
    public boolean isBearish() {
        return closePrice.compareTo(openPrice) < 0;
    }

    /** 도지 여부 (종가 == 시가) */
    public boolean isDoji() {
        return closePrice.compareTo(openPrice) == 0;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        StockCandle that = (StockCandle) o;
        return Objects.equals(symbol, that.symbol)
                && Objects.equals(timeframe, that.timeframe)
                && Objects.equals(timestamp, that.timestamp);
    }

    @Override
    public int hashCode() {
        return Objects.hash(symbol, timeframe, timestamp);
    }

    @Override
    public String toString() {
        return String.format(
                "StockCandle{symbol='%s', timeframe='%s', timestamp=%s, OHLCV=[%s,%s,%s,%s,%d]}",
                symbol, timeframe, timestamp, openPrice, highPrice, lowPrice, closePrice, volume);
    }
}
