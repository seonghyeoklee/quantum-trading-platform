package com.quantum.core.domain.model;

import static org.assertj.core.api.Assertions.*;

import com.quantum.core.domain.model.common.TimeframeCode;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

@DisplayName("주식 캔들 데이터 도메인 모델 테스트")
class StockCandleTest {

    @Test
    @DisplayName("정상적인 캔들 데이터 생성")
    void createValidCandle() {
        // given
        String symbol = "005930";
        TimeframeCode timeframe = TimeframeCode.ONE_DAY;
        LocalDateTime timestamp = LocalDateTime.of(2024, 1, 15, 15, 30);
        BigDecimal open = new BigDecimal("75000");
        BigDecimal high = new BigDecimal("76000");
        BigDecimal low = new BigDecimal("74500");
        BigDecimal close = new BigDecimal("75500");
        Long volume = 1000000L;

        // when
        StockCandle candle =
                StockCandle.create(symbol, timeframe, timestamp, open, high, low, close, volume);

        // then
        assertThat(candle.getSymbol()).isEqualTo(symbol);
        assertThat(candle.getTimeframe()).isEqualTo(timeframe);
        assertThat(candle.getTimestamp()).isEqualTo(timestamp);
        assertThat(candle.getOpenPrice()).isEqualTo(open);
        assertThat(candle.getHighPrice()).isEqualTo(high);
        assertThat(candle.getLowPrice()).isEqualTo(low);
        assertThat(candle.getClosePrice()).isEqualTo(close);
        assertThat(candle.getVolume()).isEqualTo(volume);
        assertThat(candle.getCreatedAt()).isNotNull();
    }

    @Test
    @DisplayName("캔들 패턴 분석 - 양봉")
    void analyzeBullishCandle() {
        // given
        StockCandle candle =
                StockCandle.create(
                        "005930",
                        TimeframeCode.ONE_DAY,
                        LocalDateTime.now(),
                        new BigDecimal("74000"),
                        new BigDecimal("76000"),
                        new BigDecimal("73500"),
                        new BigDecimal("75500"),
                        1000000L);

        // when & then
        assertThat(candle.isBullish()).isTrue();
        assertThat(candle.isBearish()).isFalse();
        assertThat(candle.isDoji()).isFalse();
        assertThat(candle.getBodySize()).isEqualTo(new BigDecimal("1500"));
    }

    @Test
    @DisplayName("캔들 패턴 분석 - 음봉")
    void analyzeBearishCandle() {
        // given
        StockCandle candle =
                StockCandle.create(
                        "005930",
                        TimeframeCode.ONE_DAY,
                        LocalDateTime.now(),
                        new BigDecimal("76000"),
                        new BigDecimal("76500"),
                        new BigDecimal("74000"),
                        new BigDecimal("74500"),
                        1000000L);

        // when & then
        assertThat(candle.isBullish()).isFalse();
        assertThat(candle.isBearish()).isTrue();
        assertThat(candle.isDoji()).isFalse();
        assertThat(candle.getBodySize()).isEqualTo(new BigDecimal("1500"));
    }

    @Test
    @DisplayName("도지 캔들 패턴")
    void analyzeDojiCandle() {
        // given
        StockCandle candle =
                StockCandle.create(
                        "005930",
                        TimeframeCode.ONE_DAY,
                        LocalDateTime.now(),
                        new BigDecimal("75000"),
                        new BigDecimal("75500"),
                        new BigDecimal("74500"),
                        new BigDecimal("75000"),
                        1000000L);

        // when & then
        assertThat(candle.isDoji()).isTrue();
        assertThat(candle.getBodySize()).isEqualTo(BigDecimal.ZERO);
    }

    @Test
    @DisplayName("그림자 길이 계산")
    void calculateShadowLengths() {
        // given
        StockCandle candle =
                StockCandle.create(
                        "005930",
                        TimeframeCode.ONE_DAY,
                        LocalDateTime.now(),
                        new BigDecimal("75000"),
                        new BigDecimal("76500"),
                        new BigDecimal("74000"),
                        new BigDecimal("75500"),
                        1000000L);

        // when
        BigDecimal upperShadow = candle.getUpperShadowLength();
        BigDecimal lowerShadow = candle.getLowerShadowLength();

        // then
        assertThat(upperShadow).isEqualTo(new BigDecimal("1000")); // 76500 - 75500
        assertThat(lowerShadow).isEqualTo(new BigDecimal("1000")); // 75000 - 74000
    }

    @Test
    @DisplayName("잘못된 가격으로 캔들 생성시 예외 발생")
    void createCandleWithInvalidPrices() {
        // given
        String symbol = "005930";
        TimeframeCode timeframe = TimeframeCode.ONE_DAY;
        LocalDateTime timestamp = LocalDateTime.now();
        Long volume = 1000000L;

        // when & then - 고가가 저가보다 낮은 경우
        assertThatThrownBy(
                        () ->
                                StockCandle.create(
                                        symbol,
                                        timeframe,
                                        timestamp,
                                        new BigDecimal("75000"),
                                        new BigDecimal("74000"),
                                        new BigDecimal("74500"),
                                        new BigDecimal("75000"),
                                        volume))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("High price cannot be lower than low price");

        // when & then - 시가가 범위를 벗어나는 경우
        assertThatThrownBy(
                        () ->
                                StockCandle.create(
                                        symbol,
                                        timeframe,
                                        timestamp,
                                        new BigDecimal("77000"),
                                        new BigDecimal("76000"),
                                        new BigDecimal("74000"),
                                        new BigDecimal("75000"),
                                        volume))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Open price must be between high and low prices");

        // when & then - 음수 가격
        assertThatThrownBy(
                        () ->
                                StockCandle.create(
                                        symbol,
                                        timeframe,
                                        timestamp,
                                        new BigDecimal("-1000"),
                                        new BigDecimal("76000"),
                                        new BigDecimal("74000"),
                                        new BigDecimal("75000"),
                                        volume))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Open price must be positive");
    }

    @Test
    @DisplayName("잘못된 거래량으로 캔들 생성시 예외 발생")
    void createCandleWithInvalidVolume() {
        // given
        String symbol = "005930";
        TimeframeCode timeframe = TimeframeCode.ONE_DAY;
        LocalDateTime timestamp = LocalDateTime.now();
        BigDecimal open = new BigDecimal("75000");
        BigDecimal high = new BigDecimal("76000");
        BigDecimal low = new BigDecimal("74000");
        BigDecimal close = new BigDecimal("75500");

        // when & then
        assertThatThrownBy(
                        () ->
                                StockCandle.create(
                                        symbol, timeframe, timestamp, open, high, low, close,
                                        -1000L))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Volume cannot be negative");
    }

    @Test
    @DisplayName("캔들 동등성 비교 - 심볼, 시간대, 타임스탬프 기준")
    void candleEquality() {
        // given
        LocalDateTime timestamp = LocalDateTime.of(2024, 1, 15, 15, 30);
        StockCandle candle1 =
                StockCandle.create(
                        "005930",
                        TimeframeCode.ONE_DAY,
                        timestamp,
                        new BigDecimal("75000"),
                        new BigDecimal("76000"),
                        new BigDecimal("74000"),
                        new BigDecimal("75500"),
                        1000000L);

        StockCandle candle2 =
                StockCandle.create(
                        "005930",
                        TimeframeCode.ONE_DAY,
                        timestamp,
                        new BigDecimal("74000"),
                        new BigDecimal("77000"),
                        new BigDecimal("73000"),
                        new BigDecimal("76000"),
                        2000000L);

        // when & then - 동일한 식별자 조합이면 동등
        assertThat(candle1).isEqualTo(candle2);
        assertThat(candle1.hashCode()).isEqualTo(candle2.hashCode());
    }
}
