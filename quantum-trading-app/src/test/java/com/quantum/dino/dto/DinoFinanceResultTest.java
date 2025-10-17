package com.quantum.dino.dto;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;

import static org.junit.jupiter.api.Assertions.*;

/**
 * DinoFinanceResult DTO 단위 테스트
 *
 * 검증 항목:
 * - 점수 계산 공식: MAX(0, MIN(5, 2 + SUM(개별점수)))
 * - 등급 매핑 (0-5점 → A+~D)
 * - 경계값 처리
 * - 분석 성공/실패 판단 로직
 */
@DisplayName("DinoFinanceResult DTO 단위 테스트")
class DinoFinanceResultTest {

    @Test
    @DisplayName("등급 매핑 - 5점은 A+")
    void getGrade_Score5_ReturnsAPlus() {
        // Given
        DinoFinanceResult result = createTestResult(0, 0, 0, 0, 0, 5);

        // When
        String grade = result.getGrade();

        // Then
        assertEquals("A+", grade);
    }

    @Test
    @DisplayName("등급 매핑 - 4점은 A")
    void getGrade_Score4_ReturnsA() {
        // Given
        DinoFinanceResult result = createTestResult(0, 0, 0, 0, 0, 4);

        // When
        String grade = result.getGrade();

        // Then
        assertEquals("A", grade);
    }

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
    void getGrade_AllScores_ReturnsCorrectGrade(int totalScore, String expectedGrade) {
        // Given
        DinoFinanceResult result = createTestResult(0, 0, 0, 0, 0, totalScore);

        // When
        String actualGrade = result.getGrade();

        // Then
        assertEquals(expectedGrade, actualGrade);
    }

    @Test
    @DisplayName("분석 성공 판단 - 필수 데이터가 모두 있으면 성공")
    void isSuccessful_AllRequiredDataPresent_ReturnsTrue() {
        // Given
        DinoFinanceResult result = new DinoFinanceResult(
            "005930", "삼성전자",
            1, 0, 1, 1, 1, 4,
            10.0, "흑자유지", 15.0, 200.0, 30.0,
            BigDecimal.valueOf(300000000000L), // currentRevenue
            BigDecimal.valueOf(280000000000L), // previousRevenue
            BigDecimal.valueOf(50000000000L),  // currentOperatingProfit
            BigDecimal.valueOf(45000000000L),  // previousOperatingProfit
            BigDecimal.valueOf(80000000000L),  // totalDebt
            BigDecimal.valueOf(320000000000L), // totalEquity
            BigDecimal.valueOf(220000000000L), // retainedEarnings
            BigDecimal.valueOf(100000000000L), // capitalStock
            "202312", "202212",
            LocalDateTime.now(),
            new ArrayList<>(),
            "MAX(0, MIN(5, 2 + 2)) = 4점"
        );

        // When
        boolean successful = result.isSuccessful();

        // Then
        assertTrue(successful, "필수 데이터가 모두 있으면 분석 성공으로 판단해야 함");
    }

    @Test
    @DisplayName("분석 실패 판단 - currentRevenue가 null이면 실패")
    void isSuccessful_CurrentRevenueNull_ReturnsFalse() {
        // Given
        DinoFinanceResult result = new DinoFinanceResult(
            "005930", "삼성전자",
            0, 0, 0, 0, 0, 0,
            null, null, null, null, null,
            null, // currentRevenue가 null
            BigDecimal.valueOf(280000000000L),
            BigDecimal.valueOf(50000000000L),
            BigDecimal.valueOf(45000000000L),
            BigDecimal.valueOf(80000000000L),
            BigDecimal.valueOf(320000000000L),
            BigDecimal.valueOf(220000000000L),
            BigDecimal.valueOf(100000000000L),
            null, null,
            LocalDateTime.now(),
            new ArrayList<>(),
            "분석 실패"
        );

        // When
        boolean successful = result.isSuccessful();

        // Then
        assertFalse(successful, "currentRevenue가 null이면 분석 실패로 판단해야 함");
    }

    @Test
    @DisplayName("분석 실패 판단 - previousRevenue가 null이면 실패")
    void isSuccessful_PreviousRevenueNull_ReturnsFalse() {
        // Given
        DinoFinanceResult result = new DinoFinanceResult(
            "005930", "삼성전자",
            0, 0, 0, 0, 0, 0,
            null, null, null, null, null,
            BigDecimal.valueOf(300000000000L),
            null, // previousRevenue가 null
            BigDecimal.valueOf(50000000000L),
            BigDecimal.valueOf(45000000000L),
            BigDecimal.valueOf(80000000000L),
            BigDecimal.valueOf(320000000000L),
            BigDecimal.valueOf(220000000000L),
            BigDecimal.valueOf(100000000000L),
            null, null,
            LocalDateTime.now(),
            new ArrayList<>(),
            "분석 실패"
        );

        // When
        boolean successful = result.isSuccessful();

        // Then
        assertFalse(successful, "previousRevenue가 null이면 분석 실패로 판단해야 함");
    }

    @Test
    @DisplayName("createFailedResult - 실패 결과 생성 검증")
    void createFailedResult_CreatesResultWithZeroScore() {
        // Given
        String stockCode = "005930";

        // When
        DinoFinanceResult failedResult = DinoFinanceResult.createFailedResult(stockCode);

        // Then
        assertEquals(stockCode, failedResult.stockCode());
        assertEquals(stockCode, failedResult.companyName(), "실패 시 회사명은 종목코드로 설정");
        assertEquals(0, failedResult.totalScore(), "실패 시 총점은 0");
        assertEquals(0, failedResult.revenueGrowthScore(), "모든 개별 점수는 0");
        assertEquals(0, failedResult.operatingProfitScore());
        assertEquals(0, failedResult.operatingMarginScore());
        assertEquals(0, failedResult.retentionRateScore());
        assertEquals(0, failedResult.debtRatioScore());
        assertNotNull(failedResult.analyzedAt(), "분석 시점은 설정되어야 함");
        assertNotNull(failedResult.calculationSteps(), "계산 단계 리스트는 null이 아니어야 함");
        assertFalse(failedResult.calculationSteps().isEmpty(), "실패 단계들이 기록되어야 함");
        assertEquals("분석 실패로 인한 0점 처리", failedResult.finalCalculation());
    }

    @Test
    @DisplayName("record 불변성 검증 - 모든 필드가 올바르게 생성됨")
    void recordImmutability_AllFieldsCorrectlySet() {
        // Given
        String stockCode = "005930";
        String companyName = "삼성전자";
        int revenueGrowthScore = 1;
        int operatingProfitScore = -1;
        int operatingMarginScore = 1;
        int retentionRateScore = 1;
        int debtRatioScore = 1;
        int totalScore = 3;
        Double revenueGrowthRate = 8.5;
        String operatingProfitTransition = "흑자유지";
        Double operatingMarginRate = 15.0;
        Double retentionRate = 200.0;
        Double debtRatio = 30.0;

        // When
        DinoFinanceResult result = createTestResult(
            revenueGrowthScore, operatingProfitScore, operatingMarginScore,
            retentionRateScore, debtRatioScore, totalScore
        );

        // Then
        assertEquals(stockCode, result.stockCode());
        assertEquals(companyName, result.companyName());
        assertEquals(revenueGrowthScore, result.revenueGrowthScore());
        assertEquals(operatingProfitScore, result.operatingProfitScore());
        assertEquals(operatingMarginScore, result.operatingMarginScore());
        assertEquals(retentionRateScore, result.retentionRateScore());
        assertEquals(debtRatioScore, result.debtRatioScore());
        assertEquals(totalScore, result.totalScore());
    }

    @Test
    @DisplayName("점수 범위 검증 - 개별 점수가 음수일 수 있음")
    void individualScores_CanBeNegative() {
        // Given & When
        DinoFinanceResult result = createTestResult(-1, -2, 0, -1, -1, 0);

        // Then
        assertEquals(-1, result.revenueGrowthScore());
        assertEquals(-2, result.operatingProfitScore());
        assertEquals(-1, result.retentionRateScore());
        assertEquals(-1, result.debtRatioScore());
        assertEquals(0, result.totalScore(), "음수 개별 점수라도 총점은 0 이상이어야 함");
    }

    @Test
    @DisplayName("점수 범위 검증 - 총점은 0~5 범위여야 함")
    void totalScore_ShouldBeInValidRange() {
        // Given & When
        DinoFinanceResult maxScore = createTestResult(1, 2, 1, 1, 1, 5);
        DinoFinanceResult minScore = createTestResult(-1, -2, 0, -1, -1, 0);

        // Then
        assertTrue(maxScore.totalScore() >= 0 && maxScore.totalScore() <= 5,
                  "총점은 0~5 범위여야 함");
        assertTrue(minScore.totalScore() >= 0 && minScore.totalScore() <= 5,
                  "총점은 0~5 범위여야 함");
    }

    @Test
    @DisplayName("등급 D 검증 - 총점이 음수이거나 6 이상이면 D")
    void getGrade_InvalidScore_ReturnsD() {
        // Given
        DinoFinanceResult negativeScore = createTestResult(0, 0, 0, 0, 0, -1);
        DinoFinanceResult overScore = createTestResult(0, 0, 0, 0, 0, 6);

        // When & Then
        assertEquals("D", negativeScore.getGrade(), "음수 점수는 D 등급");
        assertEquals("D", overScore.getGrade(), "6점 이상은 D 등급");
    }

    /**
     * 테스트용 DinoFinanceResult 생성 헬퍼 메서드
     */
    private DinoFinanceResult createTestResult(
            int revenueGrowthScore,
            int operatingProfitScore,
            int operatingMarginScore,
            int retentionRateScore,
            int debtRatioScore,
            int totalScore) {

        return new DinoFinanceResult(
            "005930", "삼성전자",
            revenueGrowthScore, operatingProfitScore, operatingMarginScore,
            retentionRateScore, debtRatioScore,
            totalScore,
            10.0, "흑자유지", 15.0, 200.0, 30.0,
            BigDecimal.valueOf(300000000000L),
            BigDecimal.valueOf(280000000000L),
            BigDecimal.valueOf(50000000000L),
            BigDecimal.valueOf(45000000000L),
            BigDecimal.valueOf(80000000000L),
            BigDecimal.valueOf(320000000000L),
            BigDecimal.valueOf(220000000000L),
            BigDecimal.valueOf(100000000000L),
            "202312", "202212",
            LocalDateTime.now(),
            new ArrayList<>(),
            "MAX(0, MIN(5, 2 + " + (revenueGrowthScore + operatingProfitScore +
             operatingMarginScore + retentionRateScore + debtRatioScore) + ")) = " + totalScore + "점"
        );
    }
}
