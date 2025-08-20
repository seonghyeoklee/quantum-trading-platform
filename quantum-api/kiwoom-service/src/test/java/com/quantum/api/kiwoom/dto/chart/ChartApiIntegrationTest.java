package com.quantum.api.kiwoom.dto.chart;

import com.quantum.api.kiwoom.dto.chart.timeseries.*;
import com.quantum.api.kiwoom.dto.chart.realtime.TickChartRequest;
import com.quantum.api.kiwoom.dto.chart.sector.SectorTickChartRequest;
import com.quantum.api.kiwoom.dto.chart.common.ChartApiType;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;

import java.time.LocalDate;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 차트 API DTO 통합 테스트
 * 실제 구현된 차트 API들의 기본 기능 검증
 */
class ChartApiIntegrationTest {
    
    private static final String TEST_STOCK_CODE = "005930"; // 삼성전자
    private static final String TEST_DATE = "20241108";
    private static final String TEST_SECTOR_CODE = "0001"; // 코스피
    
    @Test
    @DisplayName("일봉차트 요청 객체 생성 및 검증")
    void testDailyChartRequest() {
        // Given & When
        DailyChartRequest request = DailyChartRequest.of(TEST_STOCK_CODE, TEST_DATE);
        
        // Then
        assertNotNull(request);
        assertEquals("ka10081", request.getApiId());
        assertEquals(ChartApiType.CHART, request.getApiType());
        assertEquals(TEST_STOCK_CODE, request.getStockCode());
        assertEquals(TEST_DATE, request.getBaseDate());
        assertEquals("1", request.getUpdStkpcTp());
        
        // 검증 테스트
        assertDoesNotThrow(() -> request.validate());
    }
    
    @Test
    @DisplayName("분봉차트 요청 객체 생성 및 검증")
    void testMinuteChartRequest() {
        // Given & When
        MinuteChartRequest request = MinuteChartRequest.of(TEST_STOCK_CODE, TEST_DATE, "5");
        
        // Then
        assertNotNull(request);
        assertEquals("ka10080", request.getApiId());
        assertEquals(ChartApiType.CHART, request.getApiType());
        assertEquals(TEST_STOCK_CODE, request.getStockCode());
        assertEquals(TEST_DATE, request.getBaseDate());
        assertEquals("5", request.getTicScope());
        assertEquals("5분", request.getTicScopeDisplayName());
        assertEquals(5, request.getTicScopeAsMinutes());
        
        // 검증 테스트
        assertDoesNotThrow(() -> request.validate());
    }
    
    @Test
    @DisplayName("주봉차트 요청 객체 생성 및 검증")
    void testWeeklyChartRequest() {
        // Given & When
        WeeklyChartRequest request = WeeklyChartRequest.of(TEST_STOCK_CODE, LocalDate.of(2024, 11, 8));
        
        // Then
        assertNotNull(request);
        assertEquals("ka10082", request.getApiId());
        assertEquals(ChartApiType.CHART, request.getApiType());
        assertEquals(TEST_STOCK_CODE, request.getStockCode());
        assertEquals(TEST_DATE, request.getBaseDate());
        
        // 검증 테스트
        assertDoesNotThrow(() -> request.validate());
    }
    
    @Test
    @DisplayName("년봉차트 요청 객체 생성 및 검증")
    void testYearlyChartRequest() {
        // Given & When
        YearlyChartRequest request = YearlyChartRequest.ofYear(TEST_STOCK_CODE, 2024);
        
        // Then
        assertNotNull(request);
        assertEquals("ka10094", request.getApiId());
        assertEquals(ChartApiType.CHART, request.getApiType());
        assertEquals(TEST_STOCK_CODE, request.getStockCode());
        assertEquals("20241231", request.getBaseDate()); // 2024년 12월 31일
        
        // 검증 테스트
        assertDoesNotThrow(() -> request.validate());
    }
    
    @Test
    @DisplayName("틱차트 요청 객체 생성 및 검증")
    void testTickChartRequest() {
        // Given & When
        TickChartRequest request = TickChartRequest.ofToday(TEST_STOCK_CODE);
        
        // Then
        assertNotNull(request);
        assertEquals("ka10079", request.getApiId());
        assertEquals(ChartApiType.CHART, request.getApiType());
        assertEquals(TEST_STOCK_CODE, request.getStockCode());
        
        // 검증 테스트
        assertDoesNotThrow(() -> request.validate());
    }
    
    @Test
    @DisplayName("업종틱차트 요청 객체 생성 및 검증")
    void testSectorTickChartRequest() {
        // Given & When
        SectorTickChartRequest request = SectorTickChartRequest.ofKospiToday();
        
        // Then
        assertNotNull(request);
        assertEquals("ka20004", request.getApiId());
        assertEquals(ChartApiType.CHART, request.getApiType());
        assertEquals("0001", request.getSectorCode());
        assertEquals("코스피", request.getSectorDisplayName());
        assertTrue(request.isMajorSector());
        
        // 검증 테스트
        assertDoesNotThrow(() -> request.validate());
    }
    
    @Test
    @DisplayName("모든 차트 API의 API ID 고유성 검증")
    void testAllChartApiIdsAreUnique() {
        // Given
        String[] apiIds = {
            DailyChartRequest.of(TEST_STOCK_CODE, TEST_DATE).getApiId(),
            MinuteChartRequest.of(TEST_STOCK_CODE, TEST_DATE, "5").getApiId(),
            WeeklyChartRequest.of(TEST_STOCK_CODE, TEST_DATE).getApiId(),
            YearlyChartRequest.of(TEST_STOCK_CODE, TEST_DATE).getApiId(),
            TickChartRequest.of(TEST_STOCK_CODE, TEST_DATE).getApiId(),
            SectorTickChartRequest.of(TEST_SECTOR_CODE, TEST_DATE).getApiId()
        };
        
        // When & Then - 모든 API ID가 고유한지 확인
        assertEquals(6, java.util.Arrays.stream(apiIds).distinct().count());
        
        // 예상되는 API ID 값들 확인
        assertEquals("ka10081", apiIds[0]); // 일봉
        assertEquals("ka10080", apiIds[1]); // 분봉
        assertEquals("ka10082", apiIds[2]); // 주봉
        assertEquals("ka10094", apiIds[3]); // 년봉
        assertEquals("ka10079", apiIds[4]); // 틱
        assertEquals("ka20004", apiIds[5]); // 업종틱
    }
    
    @Test
    @DisplayName("차트 API 타입별 엔드포인트 검증")
    void testChartApiEndpoints() {
        // Given & When & Then
        assertEquals("/api/dostk/chart", ChartApiType.CHART.getEndpoint());
        assertEquals("/api/dostk/stkinfo", ChartApiType.STOCK_INFO.getEndpoint());
        
        // 대부분의 차트 API는 CHART 타입 사용
        assertEquals(ChartApiType.CHART, DailyChartRequest.of(TEST_STOCK_CODE, TEST_DATE).getApiType());
        assertEquals(ChartApiType.CHART, MinuteChartRequest.of(TEST_STOCK_CODE, TEST_DATE, "5").getApiType());
        assertEquals(ChartApiType.CHART, WeeklyChartRequest.of(TEST_STOCK_CODE, TEST_DATE).getApiType());
        assertEquals(ChartApiType.CHART, YearlyChartRequest.of(TEST_STOCK_CODE, TEST_DATE).getApiType());
        assertEquals(ChartApiType.CHART, TickChartRequest.of(TEST_STOCK_CODE, TEST_DATE).getApiType());
        assertEquals(ChartApiType.CHART, SectorTickChartRequest.of(TEST_SECTOR_CODE, TEST_DATE).getApiType());
    }
    
    @Test
    @DisplayName("잘못된 파라미터로 요청 검증 실패 테스트")
    void testValidationFailures() {
        // Given & When & Then
        
        // 빈 종목코드
        assertThrows(IllegalArgumentException.class, () -> {
            DailyChartRequest request = DailyChartRequest.of("", TEST_DATE);
            request.validate();
        });
        
        // 잘못된 날짜 형식
        assertThrows(IllegalArgumentException.class, () -> {
            DailyChartRequest request = DailyChartRequest.of(TEST_STOCK_CODE, "20241108x");
            request.validate();
        });
        
        // 잘못된 분봉 구분
        assertThrows(IllegalArgumentException.class, () -> {
            MinuteChartRequest request = MinuteChartRequest.of(TEST_STOCK_CODE, TEST_DATE, "99");
            request.validate();
        });
        
        // 빈 업종코드
        assertThrows(IllegalArgumentException.class, () -> {
            SectorTickChartRequest request = SectorTickChartRequest.of("", TEST_DATE);
            request.validate();
        });
    }
    
    @Test
    @DisplayName("편의 메서드들 동작 검증")
    void testConvenienceMethods() {
        // Given & When & Then
        
        // 오늘 기준 요청 생성
        assertDoesNotThrow(() -> {
            DailyChartRequest.ofToday(TEST_STOCK_CODE);
            MinuteChartRequest.ofToday(TEST_STOCK_CODE);
            WeeklyChartRequest.ofToday(TEST_STOCK_CODE);
            YearlyChartRequest.ofToday(TEST_STOCK_CODE);
            TickChartRequest.ofToday(TEST_STOCK_CODE);
            SectorTickChartRequest.ofKospiToday();
            SectorTickChartRequest.ofKosdaqToday();
        });
        
        // LocalDate 기준 요청 생성
        LocalDate testDate = LocalDate.of(2024, 11, 8);
        assertDoesNotThrow(() -> {
            DailyChartRequest.of(TEST_STOCK_CODE, testDate);
            MinuteChartRequest.of(TEST_STOCK_CODE, testDate);
            WeeklyChartRequest.of(TEST_STOCK_CODE, testDate);
            YearlyChartRequest.of(TEST_STOCK_CODE, testDate);
            TickChartRequest.of(TEST_STOCK_CODE, testDate);
            SectorTickChartRequest.of(TEST_SECTOR_CODE, testDate);
        });
    }
}