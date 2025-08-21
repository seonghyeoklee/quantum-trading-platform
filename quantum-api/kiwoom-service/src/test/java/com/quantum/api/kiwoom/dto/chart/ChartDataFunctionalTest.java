package com.quantum.api.kiwoom.dto.chart;

import com.quantum.api.kiwoom.dto.chart.timeseries.DailyChartData;
import com.quantum.api.kiwoom.dto.chart.timeseries.MinuteChartData;
import com.quantum.api.kiwoom.dto.chart.realtime.TickChartData;
import com.quantum.api.kiwoom.dto.chart.sector.SectorTickChartData;
import com.quantum.api.kiwoom.dto.chart.common.CandleData;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 차트 데이터 기능 테스트
 * 실제 데이터 변환 및 유틸리티 메서드 검증
 */
class ChartDataFunctionalTest {
    
    @Test
    @DisplayName("일봉 차트 데이터 변환 및 계산 기능 테스트")
    void testDailyChartDataFunctionality() {
        // Given
        DailyChartData data = DailyChartData.builder()
                .currentPrice("133600")
                .openPrice("133000")
                .highPrice("134000")
                .lowPrice("132500")
                .tradeQuantity("1,000,000")
                .tradeAmount("133,600,000,000")
                .date("20241108")
                .updateRate("+0.45")
                .previousClosePrice("133000")
                .build();
        
        // When & Then - 가격 변환
        assertEquals(new BigDecimal("133600"), data.getCurrentPriceAsDecimal());
        assertEquals(new BigDecimal("133000"), data.getOpenPriceAsDecimal());
        assertEquals(new BigDecimal("134000"), data.getHighPriceAsDecimal());
        assertEquals(new BigDecimal("132500"), data.getLowPriceAsDecimal());
        
        // 거래량/거래대금 변환
        assertEquals(1000000L, data.getTradeQuantityAsLong());
        assertEquals(new BigDecimal("133600000000"), data.getTradeAmountAsDecimal());
        
        // 날짜 변환
        assertEquals(LocalDate.of(2024, 11, 8), data.getDateAsLocalDate());
        
        // 상승/하락 판단
        assertTrue(data.isRising());
        assertFalse(data.isFalling());
        assertEquals(0.45, data.getUpdateRateAsDouble(), 0.001);
        
        // CandleData 변환
        CandleData candleData = data.toCandleData();
        assertNotNull(candleData);
        assertEquals("133600", candleData.getCurrentPrice());
        assertEquals("20241108", candleData.getDate());
    }
    
    @Test
    @DisplayName("분봉 차트 데이터 시간 처리 기능 테스트")
    void testMinuteChartDataTimeFunctionality() {
        // Given
        MinuteChartData data = MinuteChartData.builder()
                .currentPrice("133600")
                .tradeQuantity("5000")
                .contractTime("143000") // 14:30:00
                .updateRate("-0.15")
                .build();
        
        // When & Then - 시간 변환 테스트
        assertEquals("14:30:00", data.getFormattedContractTime());
        
        LocalDateTime dateTime = data.getContractTimeAsLocalDateTime("20241108");
        assertNotNull(dateTime);
        assertEquals(14, dateTime.getHour());
        assertEquals(30, dateTime.getMinute());
        assertEquals(0, dateTime.getSecond());
        
        // 상승/하락 판단
        assertFalse(data.isRising());
        assertTrue(data.isFalling());
        assertEquals(-0.15, data.getUpdateRateAsDouble(), 0.001);
    }
    
    @Test
    @DisplayName("틱차트 데이터 거래 규모 분류 기능 테스트")
    void testTickChartDataTradingSizeFunctionality() {
        // Given - 소량 거래
        TickChartData smallTick = TickChartData.builder()
                .currentPrice("133600")
                .tradeQuantity("500")
                .contractTime("143000")
                .build();
        
        // Given - 대량 거래
        TickChartData largeTick = TickChartData.builder()
                .currentPrice("133600")
                .tradeQuantity("150000")
                .contractTime("143000")
                .build();
        
        // When & Then - 거래 규모 분류
        assertEquals("SMALL", smallTick.getTickSizeCategory());
        assertEquals("EXTRA_LARGE", largeTick.getTickSizeCategory());
        
        // 거래량 변환
        assertEquals(500L, smallTick.getTradeQuantityAsLong());
        assertEquals(150000L, largeTick.getTradeQuantityAsLong());
        
        // CandleData 변환 (틱은 OHLC가 모두 현재가)
        CandleData candleData = smallTick.toCandleData();
        assertEquals("133600", candleData.getCurrentPrice());
        assertEquals("133600", candleData.getOpenPrice());
        assertEquals("133600", candleData.getHighPrice());
        assertEquals("133600", candleData.getLowPrice());
    }
    
    @Test
    @DisplayName("업종틱차트 데이터 시장 활성도 및 변동성 분류 테스트")
    void testSectorTickChartDataAnalysisFunctionality() {
        // Given - 고활성 고변동 시장
        SectorTickChartData highActivity = SectorTickChartData.builder()
                .currentIndex("2500.15")
                .tradeAmount("1500000000000") // 1조 5000억
                .updateRate("+2.5")
                .previousCloseIndex("2438.05")
                .contractTime("143000")
                .build();
        
        // Given - 저활성 저변동 시장
        SectorTickChartData lowActivity = SectorTickChartData.builder()
                .currentIndex("2500.15")
                .tradeAmount("5000000000") // 50억
                .updateRate("+0.1")
                .previousCloseIndex("2497.65")
                .build();
        
        // When & Then - 시장 활성도 분류
        assertEquals("VERY_HIGH", highActivity.getMarketActivityLevel());
        assertEquals("VERY_LOW", lowActivity.getMarketActivityLevel());
        
        // 변동성 분류
        assertEquals("VERY_HIGH", highActivity.getIndexVolatilityLevel());
        assertEquals("LOW", lowActivity.getIndexVolatilityLevel());
        
        // 지수 변환
        assertEquals(new BigDecimal("2500.15"), highActivity.getCurrentIndexAsDecimal());
        assertEquals(new BigDecimal("2438.05"), highActivity.getPreviousCloseIndexAsDecimal());
        
        // 등락 포인트 계산
        BigDecimal changePoints = highActivity.getIndexChangePoints();
        assertEquals(new BigDecimal("62.10"), changePoints);
        
        // 상승/하락 판단
        assertTrue(highActivity.isRising());
        assertTrue(lowActivity.isRising());
    }
    
    @Test
    @DisplayName("잘못된 데이터 처리 안정성 테스트")
    void testDataSafetyWithInvalidInput() {
        // Given - 빈 값들
        DailyChartData emptyData = DailyChartData.builder()
                .currentPrice("")
                .tradeQuantity(null)
                .date("invalid")
                .updateRate(null)
                .build();
        
        // When & Then - 안전한 처리
        assertEquals(BigDecimal.ZERO, emptyData.getCurrentPriceAsDecimal());
        assertEquals(0L, emptyData.getTradeQuantityAsLong());
        assertNull(emptyData.getDateAsLocalDate());
        assertFalse(emptyData.isRising());
        assertFalse(emptyData.isFalling());
        assertEquals(0.0, emptyData.getUpdateRateAsDouble());
        
        // CandleData 변환도 안전하게 처리
        CandleData candleData = emptyData.toCandleData();
        assertNotNull(candleData);
        assertEquals("", candleData.getCurrentPrice());
    }
    
    @Test
    @DisplayName("숫자 파싱 예외 상황 처리 테스트")
    void testNumberParsingExceptionHandling() {
        // Given - 잘못된 숫자 형식
        DailyChartData invalidData = DailyChartData.builder()
                .currentPrice("abc123")
                .tradeQuantity("not-a-number")
                .updateRate("++invalid")
                .build();
        
        // When & Then - 예외 없이 안전하게 처리
        assertDoesNotThrow(() -> {
            assertEquals(BigDecimal.ZERO, invalidData.getCurrentPriceAsDecimal());
            assertEquals(0L, invalidData.getTradeQuantityAsLong());
            assertEquals(0.0, invalidData.getUpdateRateAsDouble());
        });
    }
    
    @Test
    @DisplayName("시간 데이터 잘못된 형식 처리 테스트")
    void testTimeParsingExceptionHandling() {
        // Given - 잘못된 시간 형식
        MinuteChartData invalidTimeData = MinuteChartData.builder()
                .contractTime("25:99:99") // 잘못된 시간
                .build();
        
        // When & Then - 예외 없이 null 반환
        assertDoesNotThrow(() -> {
            assertNull(invalidTimeData.getContractTimeAsLocalDateTime());
            assertEquals("25:99:99", invalidTimeData.getFormattedContractTime());
        });
        
        // 너무 짧은 시간 형식
        MinuteChartData shortTimeData = MinuteChartData.builder()
                .contractTime("123") // 3자리
                .build();
        
        assertNull(shortTimeData.getContractTimeAsLocalDateTime());
        assertEquals("123", shortTimeData.getFormattedContractTime());
    }
}