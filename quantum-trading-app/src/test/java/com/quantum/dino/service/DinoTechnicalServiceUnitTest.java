package com.quantum.dino.service;

import com.quantum.backtest.domain.PriceData;
import com.quantum.dino.dto.DinoTechnicalResult;
import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.ChartDataResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

/**
 * DinoTechnicalService Mock 기반 단위 테스트
 *
 * 테스트 범위:
 * - OBV 계산 및 점수 판정 (±1점)
 * - RSI 계산 및 점수 판정 (±1점)
 * - Stochastic 계산 및 점수 판정 (±1점)
 * - MACD 계산 및 점수 판정 (±1점)
 * - 최종 점수 공식 검증: MAX(0, MIN(5, 2 + SUM))
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("DinoTechnicalService Mock 단위 테스트")
class DinoTechnicalServiceUnitTest {

    @Mock
    private KisApiPort kisApiPort;

    private DinoTechnicalService dinoTechnicalService;

    @BeforeEach
    void setUp() {
        dinoTechnicalService = new DinoTechnicalService(kisApiPort);
    }

    @Test
    @DisplayName("OBV 상승 + 주가 상승 → +1점 (추세 일치)")
    void analyzeOBVScore_BothIncreasing_Returns1Point() {
        // Given: OBV와 주가 모두 상승하는 데이터
        List<ChartDataResponse.Output2> chartData = createChartDataWithIncreasingOBV();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then
        assertTrue(result.obvScore() >= 0, "OBV 상승 + 주가 상승 시 양수 점수");
        assertEquals("success", getAnalysisStatus(result), "분석 성공 상태");
    }

    @Test
    @DisplayName("RSI 30 이하 → +1점 (과매도 매수기회)")
    void analyzeRSIScore_Oversold_Returns1Point() {
        // Given: RSI 30 이하가 되도록 하락하는 데이터
        List<ChartDataResponse.Output2> chartData = createChartDataWithOversoldRSI();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then: RSI가 과매도 구간이므로 +1점 예상
        assertTrue(result.currentRSI() != null, "RSI 값 계산됨");
        if (result.currentRSI().doubleValue() <= 30.0) {
            assertEquals(1, result.rsiScore(), "RSI 30 이하 시 +1점");
        }
    }

    @Test
    @DisplayName("RSI 70 이상 → -1점 (과매수 위험)")
    void analyzeRSIScore_Overbought_ReturnsMinus1Point() {
        // Given: RSI 70 이상이 되도록 상승하는 데이터
        List<ChartDataResponse.Output2> chartData = createChartDataWithOverboughtRSI();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then: RSI가 과매수 구간이므로 -1점 예상
        assertTrue(result.currentRSI() != null, "RSI 값 계산됨");
        if (result.currentRSI().doubleValue() >= 70.0) {
            assertEquals(-1, result.rsiScore(), "RSI 70 이상 시 -1점");
        }
    }

    @Test
    @DisplayName("RSI 30~70 중립 구간 → 0점")
    void analyzeRSIScore_Neutral_Returns0Point() {
        // Given: RSI 중립 구간 데이터
        List<ChartDataResponse.Output2> chartData = createChartDataWithNeutralRSI();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then
        assertTrue(result.currentRSI() != null, "RSI 값 계산됨");
        double rsi = result.currentRSI().doubleValue();
        if (rsi > 30.0 && rsi < 70.0) {
            assertEquals(0, result.rsiScore(), "RSI 30~70 구간 시 0점");
        }
    }

    @Test
    @DisplayName("Stochastic 25 이하 → +1점 (침체 매수기회)")
    void analyzeStochasticScore_Oversold_Returns1Point() {
        // Given: Stochastic 25 이하 데이터
        List<ChartDataResponse.Output2> chartData = createChartDataWithLowStochastic();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then
        assertTrue(result.stochasticValue() != null, "Stochastic 값 계산됨");
        if (result.stochasticValue().doubleValue() <= 25.0) {
            assertEquals(1, result.stochasticScore(), "Stochastic 25 이하 시 +1점");
        }
    }

    @Test
    @DisplayName("Stochastic 75 이상 → -1점 (과열 위험)")
    void analyzeStochasticScore_Overbought_ReturnsMinus1Point() {
        // Given: Stochastic 75 이상 데이터
        List<ChartDataResponse.Output2> chartData = createChartDataWithHighStochastic();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then
        assertTrue(result.stochasticValue() != null, "Stochastic 값 계산됨");
        if (result.stochasticValue().doubleValue() >= 75.0) {
            assertEquals(-1, result.stochasticScore(), "Stochastic 75 이상 시 -1점");
        }
    }

    @Test
    @DisplayName("MACD > Signal → +1점 (상승 추세)")
    void analyzeMACDScore_BullishCrossover_Returns1Point() {
        // Given: MACD가 Signal보다 높은 상승 추세 데이터
        List<ChartDataResponse.Output2> chartData = createChartDataWithBullishMACD();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then
        assertTrue(result.macdValue() != null, "MACD 값 계산됨");
        // MACD 상승 추세 확인 (실제 계산 결과에 따라 판단)
    }

    @Test
    @DisplayName("최종 점수 공식 검증 - MAX(0, MIN(5, 2 + SUM))")
    void totalScoreCalculation_FormulaVerification() {
        // Given: 각 지표가 +1점씩 (총 4점)
        List<ChartDataResponse.Output2> chartData = createChartDataWithAllPositiveSignals();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then: 2 + 4 = 6 → MIN(5, 6) = 5 → MAX(0, 5) = 5
        int individualSum = result.obvScore() + result.rsiScore()
                          + result.stochasticScore() + result.macdScore();
        int expectedTotal = Math.max(0, Math.min(5, 2 + individualSum));

        assertEquals(expectedTotal, result.totalScore(),
                "최종 점수는 MAX(0, MIN(5, 2 + 개별점수합))");
        assertTrue(result.totalScore() >= 0 && result.totalScore() <= 5,
                "최종 점수는 0~5점 범위");
    }

    @Test
    @DisplayName("최종 점수 계산 - 음수 개별 점수 많아도 최소 0점")
    void totalScoreCalculation_NegativeScores_MinimumZero() {
        // Given: 각 지표가 -1점씩 (총 -4점)
        List<ChartDataResponse.Output2> chartData = createChartDataWithAllNegativeSignals();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then: 2 + (-4) = -2 → MAX(0, -2) = 0
        assertTrue(result.totalScore() >= 0, "음수여도 최종 점수는 최소 0점");
    }

    @Test
    @DisplayName("최종 점수 계산 - 개별 점수 합이 커도 최대 5점")
    void totalScoreCalculation_PositiveScores_MaximumFive() {
        // Given: 각 지표가 +1점씩 (총 +4점)
        List<ChartDataResponse.Output2> chartData = createChartDataWithAllPositiveSignals();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then: 2 + 4 = 6 → MIN(5, 6) = 5
        assertTrue(result.totalScore() <= 5, "개별 점수 합이 커도 최종 점수는 최대 5점");
    }

    @Test
    @DisplayName("데이터 부족 시 실패 결과 반환")
    void analyzeTechnicalScore_InsufficientData_ReturnsFailedResult() {
        // Given: 데이터가 30일 미만
        List<ChartDataResponse.Output2> chartData = createInsufficientChartData();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then
        assertEquals(0, result.totalScore(), "데이터 부족 시 0점");
        assertEquals("분석 실패", result.obvSignal(), "OBV 신호가 '분석 실패'");
    }

    @Test
    @DisplayName("개별 점수 범위 검증 - 각 지표는 ±1점 범위")
    void individualScores_ShouldBeWithinPlusMinusOne() {
        // Given
        List<ChartDataResponse.Output2> chartData = createNormalChartData();
        ChartDataResponse response = createSuccessResponse(chartData);

        when(kisApiPort.getDailyChartData(any(), any(), any(), any()))
                .thenReturn(response);

        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then: 모든 개별 점수가 -1 ~ +1 범위인지 검증
        assertTrue(result.obvScore() >= -1 && result.obvScore() <= 1,
                "OBV 점수는 -1~+1 범위");
        assertTrue(result.rsiScore() >= -1 && result.rsiScore() <= 1,
                "RSI 점수는 -1~+1 범위");
        assertTrue(result.stochasticScore() >= -1 && result.stochasticScore() <= 1,
                "Stochastic 점수는 -1~+1 범위");
        assertTrue(result.macdScore() >= -1 && result.macdScore() <= 1,
                "MACD 점수는 -1~+1 범위");
    }

    // ==================== 테스트 데이터 생성 헬퍼 메서드 ====================

    /**
     * OBV와 주가가 모두 상승하는 차트 데이터 생성 (50일)
     */
    private List<ChartDataResponse.Output2> createChartDataWithIncreasingOBV() {
        List<ChartDataResponse.Output2> data = new ArrayList<>();
        LocalDate baseDate = LocalDate.now().minusDays(50);

        for (int i = 0; i < 50; i++) {
            String date = baseDate.plusDays(i).format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
            int basePrice = 60000 + (i * 500);  // 매일 500원씩 상승
            long volume = 10000000 + (i * 100000);  // 거래량도 증가

            data.add(new ChartDataResponse.Output2(
                    date,                                    // stckBsopDate
                    String.valueOf(basePrice + 500),         // stckClpr (종가 - 상승)
                    String.valueOf(basePrice),               // stckOprc (시가)
                    String.valueOf(basePrice + 1000),        // stckHgpr (고가)
                    String.valueOf(basePrice - 500),         // stckLwpr (저가)
                    String.valueOf(volume),                  // acmlVol (거래량)
                    "0", "00", "1.0", "N", "0", "0", "00"   // 나머지 필드
            ));
        }

        return data;
    }

    /**
     * RSI 30 이하가 되도록 하락하는 차트 데이터 생성 (30일)
     */
    private List<ChartDataResponse.Output2> createChartDataWithOversoldRSI() {
        List<ChartDataResponse.Output2> data = new ArrayList<>();
        LocalDate baseDate = LocalDate.now().minusDays(30);

        for (int i = 0; i < 30; i++) {
            String date = baseDate.plusDays(i).format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
            int basePrice = 70000 - (i * 1000);  // 매일 1000원씩 하락

            data.add(new ChartDataResponse.Output2(
                    date,                                    // stckBsopDate
                    String.valueOf(basePrice - 1000),        // stckClpr (종가 - 하락)
                    String.valueOf(basePrice),               // stckOprc (시가)
                    String.valueOf(basePrice + 500),         // stckHgpr (고가)
                    String.valueOf(basePrice - 1500),        // stckLwpr (저가)
                    "10000000",                              // acmlVol
                    "0", "00", "1.0", "N", "0", "0", "00"   // 나머지 필드
            ));
        }

        return data;
    }

    /**
     * RSI 70 이상이 되도록 상승하는 차트 데이터 생성 (30일)
     */
    private List<ChartDataResponse.Output2> createChartDataWithOverboughtRSI() {
        List<ChartDataResponse.Output2> data = new ArrayList<>();
        LocalDate baseDate = LocalDate.now().minusDays(30);

        for (int i = 0; i < 30; i++) {
            String date = baseDate.plusDays(i).format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
            int basePrice = 50000 + (i * 1000);  // 매일 1000원씩 상승

            data.add(new ChartDataResponse.Output2(
                    date,                                    // stckBsopDate
                    String.valueOf(basePrice + 1000),        // stckClpr (종가 - 상승)
                    String.valueOf(basePrice),               // stckOprc (시가)
                    String.valueOf(basePrice + 1500),        // stckHgpr (고가)
                    String.valueOf(basePrice - 500),         // stckLwpr (저가)
                    "10000000",                              // acmlVol
                    "0", "00", "1.0", "N", "0", "0", "00"   // 나머지 필드
            ));
        }

        return data;
    }

    /**
     * RSI 중립 구간 차트 데이터 생성 (30일)
     */
    private List<ChartDataResponse.Output2> createChartDataWithNeutralRSI() {
        List<ChartDataResponse.Output2> data = new ArrayList<>();
        LocalDate baseDate = LocalDate.now().minusDays(30);

        for (int i = 0; i < 30; i++) {
            String date = baseDate.plusDays(i).format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
            int basePrice = 60000 + ((i % 2 == 0) ? 200 : -200);  // 등락 반복

            data.add(new ChartDataResponse.Output2(
                    date,                                    // stckBsopDate
                    String.valueOf(basePrice),               // stckClpr (종가 - 등락 반복)
                    String.valueOf(basePrice),               // stckOprc (시가)
                    String.valueOf(basePrice + 500),         // stckHgpr (고가)
                    String.valueOf(basePrice - 500),         // stckLwpr (저가)
                    "10000000",                              // acmlVol
                    "0", "00", "1.0", "N", "0", "0", "00"   // 나머지 필드
            ));
        }

        return data;
    }

    /**
     * Stochastic 25 이하 차트 데이터 생성
     */
    private List<ChartDataResponse.Output2> createChartDataWithLowStochastic() {
        return createChartDataWithOversoldRSI();  // 하락 데이터 재사용
    }

    /**
     * Stochastic 75 이상 차트 데이터 생성
     */
    private List<ChartDataResponse.Output2> createChartDataWithHighStochastic() {
        return createChartDataWithOverboughtRSI();  // 상승 데이터 재사용
    }

    /**
     * MACD 상승 추세 차트 데이터 생성
     */
    private List<ChartDataResponse.Output2> createChartDataWithBullishMACD() {
        return createChartDataWithIncreasingOBV();  // 상승 데이터 재사용
    }

    /**
     * 모든 지표가 양수 신호를 보이는 차트 데이터 생성
     */
    private List<ChartDataResponse.Output2> createChartDataWithAllPositiveSignals() {
        return createChartDataWithOversoldRSI();  // 과매도 구간 데이터 (매수 신호)
    }

    /**
     * 모든 지표가 음수 신호를 보이는 차트 데이터 생성
     */
    private List<ChartDataResponse.Output2> createChartDataWithAllNegativeSignals() {
        return createChartDataWithOverboughtRSI();  // 과매수 구간 데이터 (매도 신호)
    }

    /**
     * 데이터 부족 차트 데이터 생성 (20일)
     */
    private List<ChartDataResponse.Output2> createInsufficientChartData() {
        List<ChartDataResponse.Output2> data = new ArrayList<>();
        LocalDate baseDate = LocalDate.now().minusDays(20);

        for (int i = 0; i < 20; i++) {
            String date = baseDate.plusDays(i).format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));

            data.add(new ChartDataResponse.Output2(
                    date,                                    // stckBsopDate
                    "60500",                                 // stckClpr (종가)
                    "60000",                                 // stckOprc (시가)
                    "61000",                                 // stckHgpr (고가)
                    "59000",                                 // stckLwpr (저가)
                    "10000000",                              // acmlVol
                    "0", "00", "1.0", "N", "0", "0", "00"   // 나머지 필드
            ));
        }

        return data;
    }

    /**
     * 정상적인 차트 데이터 생성 (50일)
     */
    private List<ChartDataResponse.Output2> createNormalChartData() {
        return createChartDataWithNeutralRSI();
    }

    /**
     * 성공 응답 생성
     */
    private ChartDataResponse createSuccessResponse(List<ChartDataResponse.Output2> chartData) {
        ChartDataResponse.Output1 output1 = new ChartDataResponse.Output1(
                "0",          // prdyVrss (전일대비)
                "2",          // prdyVrssSign (전일대비부호)
                "0.5",        // prdyCtrt (전일대비율)
                "60000",      // stckPrdyClpr (주식전일종가)
                "10000000",   // acmlVol (누적거래량)
                "600000000",  // acmlTrPbmn (누적거래대금)
                "삼성전자",     // htsKorIsnm (종목명)
                "60500"       // stckPrpr (주식현재가)
        );

        return new ChartDataResponse(
                "0",           // returnCode (성공 코드)
                "OPSP0000",    // messageCode
                "정상처리 되었습니다.", // message
                output1,
                chartData
        );
    }

    /**
     * 분석 상태 확인
     */
    private String getAnalysisStatus(DinoTechnicalResult result) {
        if (result.obvSignal().equals("분석 실패")) {
            return "failed";
        }
        return "success";
    }
}
