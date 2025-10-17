package com.quantum.dino.dto;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;

/**
 * DinoPriceResult DTO 단위 테스트
 *
 * 검증 항목:
 * - 트렌드/모멘텀/변동성/지지저항 점수 검증
 * - 총점 범위 검증 (0~5점)
 * - 등급 매핑
 * - 포맷팅 메서드 (가격 변화율, 금액 표시)
 */
@DisplayName("DinoPriceResult DTO 단위 테스트")
class DinoPriceResultTest {

    @ParameterizedTest
    @CsvSource({
        "5, A+",
        "4, A",
        "3, B+",
        "2, B",
        "1, C+",
        "0, C",
        "-1, D"
    })
    @DisplayName("등급 매핑 - 모든 점수별 등급 검증")
    void getPriceGrade_AllScores_ReturnsCorrectGrade(int totalScore, String expectedGrade) {
        // Given
        DinoPriceResult result = createTestResult(0, 0, 0, 0, totalScore);

        // When
        String actualGrade = result.getPriceGrade();

        // Then
        assertEquals(expectedGrade, actualGrade);
    }

    @Test
    @DisplayName("총점 범위 검증 - 0~5점이면 유효")
    void isValidScore_ScoreInRange_ReturnsTrue() {
        // Given
        DinoPriceResult validMin = createTestResult(0, 0, 0, 0, 0);
        DinoPriceResult validMax = createTestResult(2, 1, 1, 1, 5);
        DinoPriceResult validMid = createTestResult(1, 1, 0, 1, 3);

        // When & Then
        assertTrue(validMin.isValidScore(), "0점은 유효");
        assertTrue(validMax.isValidScore(), "5점은 유효");
        assertTrue(validMid.isValidScore(), "3점은 유효");
    }

    @Test
    @DisplayName("총점 범위 검증 - 음수이거나 6 이상이면 무효")
    void isValidScore_ScoreOutOfRange_ReturnsFalse() {
        // Given
        DinoPriceResult negativeScore = createTestResult(0, 0, 0, 0, -1);
        DinoPriceResult overScore = createTestResult(0, 0, 0, 0, 6);

        // When & Then
        assertFalse(negativeScore.isValidScore(), "-1점은 무효");
        assertFalse(overScore.isValidScore(), "6점은 무효");
    }

    @ParameterizedTest
    @CsvSource({
        "5, '강한 가격 상승 신호 - 매수 관점에서 긍정적'",
        "4, '강한 가격 상승 신호 - 매수 관점에서 긍정적'",
        "3, '약한 가격 상승 신호 - 신중한 접근 권장'",
        "2, '약한 가격 상승 신호 - 신중한 접근 권장'",
        "1, '가격 중립 상태 - 추가 모니터링 필요'",
        "0, '가격 중립 상태 - 추가 모니터링 필요'",
        "-1, '가격 하락 신호 - 리스크 관리 필요'"
    })
    @DisplayName("종합 평가 메시지 - 점수별 적절한 메시지 반환")
    void getPriceSummary_AllScores_ReturnsCorrectMessage(int totalScore, String expectedMessage) {
        // Given
        DinoPriceResult result = createTestResult(0, 0, 0, 0, totalScore);

        // When
        String actualMessage = result.getPriceSummary();

        // Then
        assertEquals(expectedMessage, actualMessage);
    }

    @Test
    @DisplayName("가격 변화율 포맷팅 - 양수는 + 기호 포함")
    void getFormattedChangeRate_PositiveValue_IncludesPlusSign() {
        // Given
        DinoPriceResult result = createTestResultWithPriceData(
            BigDecimal.valueOf(60000),
            BigDecimal.valueOf(1000),
            BigDecimal.valueOf(1.69)
        );

        // When
        String formattedRate = result.getFormattedChangeRate();

        // Then
        assertEquals("+1.69%", formattedRate);
    }

    @Test
    @DisplayName("가격 변화율 포맷팅 - 음수는 - 기호 유지")
    void getFormattedChangeRate_NegativeValue_KeepsMinusSign() {
        // Given
        DinoPriceResult result = createTestResultWithPriceData(
            BigDecimal.valueOf(60000),
            BigDecimal.valueOf(-1000),
            BigDecimal.valueOf(-1.64)
        );

        // When
        String formattedRate = result.getFormattedChangeRate();

        // Then
        assertEquals("-1.64%", formattedRate);
    }

    @Test
    @DisplayName("가격 변화율 포맷팅 - null이면 N/A 반환")
    void getFormattedChangeRate_NullValue_ReturnsNA() {
        // Given
        DinoPriceResult result = createTestResultWithPriceData(
            BigDecimal.valueOf(60000),
            BigDecimal.valueOf(1000),
            null
        );

        // When
        String formattedRate = result.getFormattedChangeRate();

        // Then
        assertEquals("N/A", formattedRate);
    }

    @Test
    @DisplayName("가격 변화액 포맷팅 - 양수는 + 기호와 원 단위 포함")
    void getFormattedPriceChange_PositiveValue_IncludesPlusSignAndWon() {
        // Given
        DinoPriceResult result = createTestResultWithPriceData(
            BigDecimal.valueOf(60000),
            BigDecimal.valueOf(1000),
            BigDecimal.valueOf(1.69)
        );

        // When
        String formattedChange = result.getFormattedPriceChange();

        // Then
        assertEquals("+1000원", formattedChange);
    }

    @Test
    @DisplayName("가격 변화액 포맷팅 - 음수는 - 기호와 원 단위 포함")
    void getFormattedPriceChange_NegativeValue_KeepsMinusSignAndWon() {
        // Given
        DinoPriceResult result = createTestResultWithPriceData(
            BigDecimal.valueOf(60000),
            BigDecimal.valueOf(-1000),
            BigDecimal.valueOf(-1.64)
        );

        // When
        String formattedChange = result.getFormattedPriceChange();

        // Then
        assertEquals("-1000원", formattedChange);
    }

    @Test
    @DisplayName("가격 변화액 포맷팅 - null이면 N/A 반환")
    void getFormattedPriceChange_NullValue_ReturnsNA() {
        // Given
        DinoPriceResult result = createTestResultWithPriceData(
            BigDecimal.valueOf(60000),
            null,
            BigDecimal.valueOf(1.69)
        );

        // When
        String formattedChange = result.getFormattedPriceChange();

        // Then
        assertEquals("N/A", formattedChange);
    }

    @Test
    @DisplayName("createFailedResult - 실패 결과 생성 검증")
    void createFailedResult_CreatesResultWithZeroScore() {
        // Given
        String stockCode = "005930";

        // When
        DinoPriceResult failedResult = DinoPriceResult.createFailedResult(stockCode);

        // Then
        assertEquals(stockCode, failedResult.stockCode());
        assertEquals(stockCode, failedResult.companyName(), "실패 시 회사명은 종목코드로 설정");
        assertEquals(0, failedResult.totalScore(), "실패 시 총점은 0");
        assertEquals(0, failedResult.trendScore(), "모든 개별 점수는 0");
        assertEquals(0, failedResult.momentumScore());
        assertEquals(0, failedResult.volatilityScore());
        assertEquals(0, failedResult.supportResistanceScore());
        assertNull(failedResult.currentPrice(), "실패 시 가격 데이터는 null");
        assertNull(failedResult.priceChange());
        assertNull(failedResult.priceChangeRate());
        assertEquals("분석 실패", failedResult.trendSignal());
        assertEquals("분석 실패", failedResult.momentumSignal());
        assertEquals("분석 실패", failedResult.volatilitySignal());
        assertEquals("분석 실패", failedResult.supportResistanceSignal());
        assertNotNull(failedResult.analysisDateTime(), "분석 시점은 설정되어야 함");
    }

    @Test
    @DisplayName("개별 점수 범위 검증 - 트렌드는 -2~+2점")
    void trendScore_ShouldBeInValidRange() {
        // Given & When
        DinoPriceResult maxTrend = createTestResult(2, 0, 0, 0, 4);
        DinoPriceResult minTrend = createTestResult(-2, 0, 0, 0, 0);

        // Then
        assertEquals(2, maxTrend.trendScore());
        assertEquals(-2, minTrend.trendScore());
        assertTrue(maxTrend.trendScore() >= -2 && maxTrend.trendScore() <= 2);
        assertTrue(minTrend.trendScore() >= -2 && minTrend.trendScore() <= 2);
    }

    @Test
    @DisplayName("개별 점수 범위 검증 - 모멘텀/변동성/지지저항은 각 ±1점")
    void otherScores_ShouldBeWithinPlusMinusOne() {
        // Given & When
        DinoPriceResult result = createTestResult(0, 1, -1, 1, 3);

        // Then
        assertTrue(result.momentumScore() >= -1 && result.momentumScore() <= 1);
        assertTrue(result.volatilityScore() >= -1 && result.volatilityScore() <= 1);
        assertTrue(result.supportResistanceScore() >= -1 && result.supportResistanceScore() <= 1);
    }

    @Test
    @DisplayName("record 불변성 검증 - 모든 필드가 올바르게 생성됨")
    void recordImmutability_AllFieldsCorrectlySet() {
        // Given
        String stockCode = "005930";
        String companyName = "삼성전자";
        int trendScore = 2;
        int momentumScore = 1;
        int volatilityScore = -1;
        int supportResistanceScore = 1;
        int totalScore = 5;
        BigDecimal currentPrice = BigDecimal.valueOf(60000);
        BigDecimal priceChange = BigDecimal.valueOf(1000);
        BigDecimal priceChangeRate = BigDecimal.valueOf(1.69);

        // When
        DinoPriceResult result = new DinoPriceResult(
            stockCode, companyName,
            trendScore, momentumScore, volatilityScore, supportResistanceScore, totalScore,
            currentPrice, priceChange, priceChangeRate,
            BigDecimal.valueOf(5.0),   // shortTermTrend
            BigDecimal.valueOf(10.0),  // mediumTermTrend
            BigDecimal.valueOf(2.5),   // volatility
            BigDecimal.valueOf(58000), // supportLevel
            BigDecimal.valueOf(62000), // resistanceLevel
            "상승 추세", "강한 모멘텀", "안정적", "저항 돌파",
            LocalDateTime.now()
        );

        // Then
        assertEquals(stockCode, result.stockCode());
        assertEquals(companyName, result.companyName());
        assertEquals(trendScore, result.trendScore());
        assertEquals(momentumScore, result.momentumScore());
        assertEquals(volatilityScore, result.volatilityScore());
        assertEquals(supportResistanceScore, result.supportResistanceScore());
        assertEquals(totalScore, result.totalScore());
        assertEquals(currentPrice, result.currentPrice());
        assertEquals(priceChange, result.priceChange());
        assertEquals(priceChangeRate, result.priceChangeRate());
        assertNotNull(result.analysisDateTime());
    }

    /**
     * 테스트용 DinoPriceResult 생성 헬퍼 메서드 (점수만)
     */
    private DinoPriceResult createTestResult(
            int trendScore,
            int momentumScore,
            int volatilityScore,
            int supportResistanceScore,
            int totalScore) {

        return new DinoPriceResult(
            "005930", "삼성전자",
            trendScore, momentumScore, volatilityScore, supportResistanceScore, totalScore,
            BigDecimal.valueOf(60000), BigDecimal.valueOf(1000), BigDecimal.valueOf(1.69),
            BigDecimal.valueOf(5.0), BigDecimal.valueOf(10.0), BigDecimal.valueOf(2.5),
            BigDecimal.valueOf(58000), BigDecimal.valueOf(62000),
            "테스트 트렌드", "테스트 모멘텀", "테스트 변동성", "테스트 지지저항",
            LocalDateTime.now()
        );
    }

    /**
     * 테스트용 DinoPriceResult 생성 헬퍼 메서드 (가격 데이터 포함)
     */
    private DinoPriceResult createTestResultWithPriceData(
            BigDecimal currentPrice,
            BigDecimal priceChange,
            BigDecimal priceChangeRate) {

        return new DinoPriceResult(
            "005930", "삼성전자",
            0, 0, 0, 0, 0,
            currentPrice, priceChange, priceChangeRate,
            BigDecimal.valueOf(5.0), BigDecimal.valueOf(10.0), BigDecimal.valueOf(2.5),
            BigDecimal.valueOf(58000), BigDecimal.valueOf(62000),
            "테스트", "테스트", "테스트", "테스트",
            LocalDateTime.now()
        );
    }
}
