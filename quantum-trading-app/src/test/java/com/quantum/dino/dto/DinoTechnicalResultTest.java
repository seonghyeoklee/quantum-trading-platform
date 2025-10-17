package com.quantum.dino.dto;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;

/**
 * DinoTechnicalResult DTO 단위 테스트
 *
 * 검증 항목:
 * - 4개 지표 각 ±1점 범위 검증
 * - 총점 계산 공식: MAX(0, MIN(5, 2 + SUM(개별점수)))
 * - 등급 매핑
 * - 신호 메시지 생성 로직
 */
@DisplayName("DinoTechnicalResult DTO 단위 테스트")
class DinoTechnicalResultTest {

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
    void getTechnicalGrade_AllScores_ReturnsCorrectGrade(int totalScore, String expectedGrade) {
        // Given
        DinoTechnicalResult result = createTestResult(0, 0, 0, 0, totalScore);

        // When
        String actualGrade = result.getTechnicalGrade();

        // Then
        assertEquals(expectedGrade, actualGrade);
    }

    @Test
    @DisplayName("총점 범위 검증 - 0~5점이면 유효")
    void isValidScore_ScoreInRange_ReturnsTrue() {
        // Given
        DinoTechnicalResult validMin = createTestResult(0, 0, 0, 0, 0);
        DinoTechnicalResult validMax = createTestResult(1, 1, 1, 1, 5);
        DinoTechnicalResult validMid = createTestResult(1, 0, -1, 1, 3);

        // When & Then
        assertTrue(validMin.isValidScore(), "0점은 유효");
        assertTrue(validMax.isValidScore(), "5점은 유효");
        assertTrue(validMid.isValidScore(), "3점은 유효");
    }

    @Test
    @DisplayName("총점 범위 검증 - 음수이거나 6 이상이면 무효")
    void isValidScore_ScoreOutOfRange_ReturnsFalse() {
        // Given
        DinoTechnicalResult negativeScore = createTestResult(0, 0, 0, 0, -1);
        DinoTechnicalResult overScore = createTestResult(0, 0, 0, 0, 6);

        // When & Then
        assertFalse(negativeScore.isValidScore(), "-1점은 무효");
        assertFalse(overScore.isValidScore(), "6점은 무효");
    }

    @Test
    @DisplayName("개별 점수 범위 검증 - 각 지표는 ±1점 범위")
    void individualScores_ShouldBeWithinPlusMinusOne() {
        // Given & When
        DinoTechnicalResult allPositive = createTestResult(1, 1, 1, 1, 5);
        DinoTechnicalResult allNegative = createTestResult(-1, -1, -1, -1, 0);
        DinoTechnicalResult mixed = createTestResult(1, -1, 1, 0, 3);

        // Then
        // 모든 개별 점수가 -1 ~ +1 범위인지 검증
        assertTrue(allPositive.obvScore() >= -1 && allPositive.obvScore() <= 1);
        assertTrue(allPositive.rsiScore() >= -1 && allPositive.rsiScore() <= 1);
        assertTrue(allPositive.stochasticScore() >= -1 && allPositive.stochasticScore() <= 1);
        assertTrue(allPositive.macdScore() >= -1 && allPositive.macdScore() <= 1);

        assertTrue(allNegative.obvScore() >= -1 && allNegative.obvScore() <= 1);
        assertTrue(allNegative.rsiScore() >= -1 && allNegative.rsiScore() <= 1);
        assertTrue(allNegative.stochasticScore() >= -1 && allNegative.stochasticScore() <= 1);
        assertTrue(allNegative.macdScore() >= -1 && allNegative.macdScore() <= 1);

        assertTrue(mixed.obvScore() >= -1 && mixed.obvScore() <= 1);
        assertTrue(mixed.rsiScore() >= -1 && mixed.rsiScore() <= 1);
        assertTrue(mixed.stochasticScore() >= -1 && mixed.stochasticScore() <= 1);
        assertTrue(mixed.macdScore() >= -1 && mixed.macdScore() <= 1);
    }

    @ParameterizedTest
    @CsvSource({
        "5, '강한 상승 신호 - 매수 관점에서 긍정적'",
        "4, '강한 상승 신호 - 매수 관점에서 긍정적'",
        "3, '약한 상승 신호 - 관망 후 진입 고려'",
        "2, '약한 상승 신호 - 관망 후 진입 고려'",
        "1, '중립 상태 - 추가 신호 확인 필요'",
        "0, '중립 상태 - 추가 신호 확인 필요'",
        "-1, '약세 신호 - 하락 리스크 주의'"
    })
    @DisplayName("종합 평가 메시지 - 점수별 적절한 메시지 반환")
    void getTechnicalSummary_AllScores_ReturnsCorrectMessage(int totalScore, String expectedMessage) {
        // Given
        DinoTechnicalResult result = createTestResult(0, 0, 0, 0, totalScore);

        // When
        String actualMessage = result.getTechnicalSummary();

        // Then
        assertEquals(expectedMessage, actualMessage);
    }

    @Test
    @DisplayName("createFailedResult - 실패 결과 생성 검증")
    void createFailedResult_CreatesResultWithZeroScore() {
        // Given
        String stockCode = "005930";
        String companyName = "삼성전자";

        // When
        DinoTechnicalResult failedResult = DinoTechnicalResult.createFailedResult(stockCode, companyName);

        // Then
        assertEquals(stockCode, failedResult.stockCode());
        assertEquals(companyName, failedResult.companyName());
        assertEquals(0, failedResult.totalScore(), "실패 시 총점은 0");
        assertEquals(0, failedResult.obvScore(), "모든 개별 점수는 0");
        assertEquals(0, failedResult.rsiScore());
        assertEquals(0, failedResult.stochasticScore());
        assertEquals(0, failedResult.macdScore());
        assertNull(failedResult.obvValue(), "실패 시 지표 값은 null");
        assertNull(failedResult.currentRSI());
        assertNull(failedResult.stochasticValue());
        assertNull(failedResult.macdValue());
        assertEquals("분석 실패", failedResult.obvSignal());
        assertEquals("분석 실패", failedResult.rsiSignal());
        assertEquals("분석 실패", failedResult.stochasticSignal());
        assertEquals("분석 실패", failedResult.macdSignal());
        assertNotNull(failedResult.analysisDateTime(), "분석 시점은 설정되어야 함");
    }

    @Test
    @DisplayName("record 불변성 검증 - 모든 필드가 올바르게 생성됨")
    void recordImmutability_AllFieldsCorrectlySet() {
        // Given
        String stockCode = "005930";
        String companyName = "삼성전자";
        int obvScore = 1;
        int rsiScore = -1;
        int stochasticScore = 1;
        int macdScore = 0;
        int totalScore = 3;
        BigDecimal obvValue = BigDecimal.valueOf(1000000);
        BigDecimal currentRSI = BigDecimal.valueOf(55.5);
        BigDecimal stochasticValue = BigDecimal.valueOf(60.0);
        BigDecimal macdValue = BigDecimal.valueOf(0.5);
        String obvSignal = "상승 추세";
        String rsiSignal = "과매수 구간";
        String stochasticSignal = "매수 신호";
        String macdSignal = "중립";

        // When
        DinoTechnicalResult result = new DinoTechnicalResult(
            stockCode, companyName,
            obvScore, rsiScore, stochasticScore, macdScore, totalScore,
            obvValue, currentRSI, stochasticValue, macdValue,
            obvSignal, rsiSignal, stochasticSignal, macdSignal,
            LocalDateTime.now()
        );

        // Then
        assertEquals(stockCode, result.stockCode());
        assertEquals(companyName, result.companyName());
        assertEquals(obvScore, result.obvScore());
        assertEquals(rsiScore, result.rsiScore());
        assertEquals(stochasticScore, result.stochasticScore());
        assertEquals(macdScore, result.macdScore());
        assertEquals(totalScore, result.totalScore());
        assertEquals(obvValue, result.obvValue());
        assertEquals(currentRSI, result.currentRSI());
        assertEquals(stochasticValue, result.stochasticValue());
        assertEquals(macdValue, result.macdValue());
        assertEquals(obvSignal, result.obvSignal());
        assertEquals(rsiSignal, result.rsiSignal());
        assertEquals(stochasticSignal, result.stochasticSignal());
        assertEquals(macdSignal, result.macdSignal());
        assertNotNull(result.analysisDateTime());
    }

    @Test
    @DisplayName("점수 공식 검증 - MAX(0, MIN(5, 2 + SUM(개별점수)))")
    void scoreCalculationFormula_Verification() {
        // Given: 개별 점수 합이 1인 경우 (1 + 0 + (-1) + 1 = 1)
        int obvScore = 1;
        int rsiScore = 0;
        int stochasticScore = -1;
        int macdScore = 1;
        int individualSum = obvScore + rsiScore + stochasticScore + macdScore;
        int expectedTotal = Math.max(0, Math.min(5, 2 + individualSum));

        // When
        DinoTechnicalResult result = createTestResult(obvScore, rsiScore, stochasticScore, macdScore, expectedTotal);

        // Then
        assertEquals(3, result.totalScore(), "2 + 1 = 3점이어야 함");
        assertEquals(expectedTotal, result.totalScore());
    }

    @Test
    @DisplayName("점수 공식 검증 - 음수 개별 점수가 많아도 총점은 최소 0")
    void scoreCalculationFormula_NegativeScores_MinimumZero() {
        // Given: 개별 점수 합이 -4인 경우 (모두 -1)
        int obvScore = -1;
        int rsiScore = -1;
        int stochasticScore = -1;
        int macdScore = -1;
        int individualSum = obvScore + rsiScore + stochasticScore + macdScore; // -4
        int expectedTotal = Math.max(0, Math.min(5, 2 + individualSum)); // MAX(0, MIN(5, -2)) = 0

        // When
        DinoTechnicalResult result = createTestResult(obvScore, rsiScore, stochasticScore, macdScore, expectedTotal);

        // Then
        assertEquals(0, result.totalScore(), "음수 합이어도 총점은 0 이상이어야 함");
    }

    @Test
    @DisplayName("점수 공식 검증 - 개별 점수 합이 커도 총점은 최대 5")
    void scoreCalculationFormula_PositiveScores_MaximumFive() {
        // Given: 개별 점수 합이 4인 경우 (모두 +1)
        int obvScore = 1;
        int rsiScore = 1;
        int stochasticScore = 1;
        int macdScore = 1;
        int individualSum = obvScore + rsiScore + stochasticScore + macdScore; // 4
        int expectedTotal = Math.max(0, Math.min(5, 2 + individualSum)); // MAX(0, MIN(5, 6)) = 5

        // When
        DinoTechnicalResult result = createTestResult(obvScore, rsiScore, stochasticScore, macdScore, expectedTotal);

        // Then
        assertEquals(5, result.totalScore(), "개별 점수 합이 커도 총점은 5 이하여야 함");
    }

    /**
     * 테스트용 DinoTechnicalResult 생성 헬퍼 메서드
     */
    private DinoTechnicalResult createTestResult(
            int obvScore,
            int rsiScore,
            int stochasticScore,
            int macdScore,
            int totalScore) {

        return new DinoTechnicalResult(
            "005930", "삼성전자",
            obvScore, rsiScore, stochasticScore, macdScore, totalScore,
            BigDecimal.valueOf(1000000), // obvValue
            BigDecimal.valueOf(55.5),    // currentRSI
            BigDecimal.valueOf(60.0),    // stochasticValue
            BigDecimal.valueOf(0.5),     // macdValue
            "테스트 OBV 신호",
            "테스트 RSI 신호",
            "테스트 Stochastic 신호",
            "테스트 MACD 신호",
            LocalDateTime.now()
        );
    }
}
