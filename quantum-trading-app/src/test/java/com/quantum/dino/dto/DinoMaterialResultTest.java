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
 * DinoMaterialResult DTO 단위 테스트
 *
 * 검증 항목:
 * - 배당/수급/심리/어닝서프라이즈 점수 검증
 * - 총점 범위 검증 (0~5점)
 * - 등급 매핑
 * - 재료 강도 및 지속성 계산 로직
 * - 포맷팅 메서드
 */
@DisplayName("DinoMaterialResult DTO 단위 테스트")
class DinoMaterialResultTest {

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
    void getMaterialGrade_AllScores_ReturnsCorrectGrade(int totalScore, String expectedGrade) {
        // Given
        DinoMaterialResult result = createTestResult(0, 0, 0, 0, totalScore);

        // When
        String actualGrade = result.getMaterialGrade();

        // Then
        assertEquals(expectedGrade, actualGrade);
    }

    @Test
    @DisplayName("총점 범위 검증 - 0~5점이면 유효")
    void isValidScore_ScoreInRange_ReturnsTrue() {
        // Given
        DinoMaterialResult validMin = createTestResult(0, 0, 0, 0, 0);
        DinoMaterialResult validMax = createTestResult(1, 1, 1, 1, 5);
        DinoMaterialResult validMid = createTestResult(1, 1, 0, 0, 3);

        // When & Then
        assertTrue(validMin.isValidScore(), "0점은 유효");
        assertTrue(validMax.isValidScore(), "5점은 유효");
        assertTrue(validMid.isValidScore(), "3점은 유효");
    }

    @Test
    @DisplayName("총점 범위 검증 - 음수이거나 6 이상이면 무효")
    void isValidScore_ScoreOutOfRange_ReturnsFalse() {
        // Given
        DinoMaterialResult negativeScore = createTestResult(0, 0, 0, 0, -1);
        DinoMaterialResult overScore = createTestResult(0, 0, 0, 0, 6);

        // When & Then
        assertFalse(negativeScore.isValidScore(), "-1점은 무효");
        assertFalse(overScore.isValidScore(), "6점은 무효");
    }

    @ParameterizedTest
    @CsvSource({
        "5, '강력한 호재 - 매수 관점에서 매우 긍정적'",
        "4, '강력한 호재 - 매수 관점에서 매우 긍정적'",
        "3, '약한 호재 - 긍정적 요소 존재'",
        "2, '약한 호재 - 긍정적 요소 존재'",
        "1, '재료 중립 - 특별한 호재/악재 없음'",
        "0, '재료 중립 - 특별한 호재/악재 없음'",
        "-1, '악재 요소 - 주의 깊은 관찰 필요'"
    })
    @DisplayName("종합 평가 메시지 - 점수별 적절한 메시지 반환")
    void getMaterialSummary_AllScores_ReturnsCorrectMessage(int totalScore, String expectedMessage) {
        // Given
        DinoMaterialResult result = createTestResult(0, 0, 0, 0, totalScore);

        // When
        String actualMessage = result.getMaterialSummary();

        // Then
        assertEquals(expectedMessage, actualMessage);
    }

    @Test
    @DisplayName("배당 임팩트 포맷팅 - 정상 값이면 % 포함")
    void getFormattedDividendImpact_ValidValue_IncludesPercentage() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(
            BigDecimal.valueOf(3.5), null, null, null
        );

        // When
        String formatted = result.getFormattedDividendImpact();

        // Then
        assertEquals("3.5%", formatted);
    }

    @Test
    @DisplayName("배당 임팩트 포맷팅 - null이면 N/A 반환")
    void getFormattedDividendImpact_NullValue_ReturnsNA() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(null, null, null, null);

        // When
        String formatted = result.getFormattedDividendImpact();

        // Then
        assertEquals("N/A", formatted);
    }

    @Test
    @DisplayName("투자자 트렌드 포맷팅 - 양수는 + 기호 포함")
    void getFormattedInvestorTrend_PositiveValue_IncludesPlusSign() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(
            null, BigDecimal.valueOf(5.2), null, null
        );

        // When
        String formatted = result.getFormattedInvestorTrend();

        // Then
        assertEquals("+5.2%", formatted);
    }

    @Test
    @DisplayName("투자자 트렌드 포맷팅 - 음수는 - 기호 유지")
    void getFormattedInvestorTrend_NegativeValue_KeepsMinusSign() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(
            null, BigDecimal.valueOf(-3.1), null, null
        );

        // When
        String formatted = result.getFormattedInvestorTrend();

        // Then
        assertEquals("-3.1%", formatted);
    }

    @Test
    @DisplayName("투자자 트렌드 포맷팅 - null이면 N/A 반환")
    void getFormattedInvestorTrend_NullValue_ReturnsNA() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(null, null, null, null);

        // When
        String formatted = result.getFormattedInvestorTrend();

        // Then
        assertEquals("N/A", formatted);
    }

    @Test
    @DisplayName("심리 지수 포맷팅 - 정상 값이면 문자열 반환")
    void getFormattedPsychologyIndex_ValidValue_ReturnsString() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(
            null, null, BigDecimal.valueOf(65.5), null
        );

        // When
        String formatted = result.getFormattedPsychologyIndex();

        // Then
        assertEquals("65.5", formatted);
    }

    @Test
    @DisplayName("심리 지수 포맷팅 - null이면 N/A 반환")
    void getFormattedPsychologyIndex_NullValue_ReturnsNA() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(null, null, null, null);

        // When
        String formatted = result.getFormattedPsychologyIndex();

        // Then
        assertEquals("N/A", formatted);
    }

    @Test
    @DisplayName("재료 지속성 평가 - 30일 이상은 장기 재료")
    void getMaterialDurability_OverThirtyDays_ReturnsLongTerm() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(
            null, null, null, BigDecimal.valueOf(35)
        );

        // When
        String durability = result.getMaterialDurability();

        // Then
        assertEquals("장기 재료 (30일+)", durability);
    }

    @Test
    @DisplayName("재료 지속성 평가 - 7~30일은 중기 재료")
    void getMaterialDurability_SevenToThirtyDays_ReturnsMediumTerm() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(
            null, null, null, BigDecimal.valueOf(15)
        );

        // When
        String durability = result.getMaterialDurability();

        // Then
        assertEquals("중기 재료 (15일)", durability);
    }

    @Test
    @DisplayName("재료 지속성 평가 - 7일 미만은 단기 재료")
    void getMaterialDurability_LessThanSevenDays_ReturnsShortTerm() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(
            null, null, null, BigDecimal.valueOf(3)
        );

        // When
        String durability = result.getMaterialDurability();

        // Then
        assertEquals("단기 재료 (3일)", durability);
    }

    @Test
    @DisplayName("재료 지속성 평가 - null이면 N/A 반환")
    void getMaterialDurability_NullValue_ReturnsNA() {
        // Given
        DinoMaterialResult result = createTestResultWithDetails(null, null, null, null);

        // When
        String durability = result.getMaterialDurability();

        // Then
        assertEquals("N/A", durability);
    }

    @Test
    @DisplayName("뉴스 밸런스 - 긍정 70% 이상이면 긍정 우세")
    void getNewsBalance_PositiveOver70Percent_ReturnsPositiveDominant() {
        // Given
        DinoMaterialResult result = createTestResultWithNews(7, 3); // 70% 긍정

        // When
        String balance = result.getNewsBalance();

        // Then
        assertEquals("긍정 우세 (70%)", balance);
    }

    @Test
    @DisplayName("뉴스 밸런스 - 긍정 30~70%이면 혼재")
    void getNewsBalance_PositiveBetween30And70Percent_ReturnsMixed() {
        // Given
        DinoMaterialResult result = createTestResultWithNews(5, 5); // 50% 긍정

        // When
        String balance = result.getNewsBalance();

        // Then
        assertEquals("혼재 (긍정 50%)", balance);
    }

    @Test
    @DisplayName("뉴스 밸런스 - 긍정 30% 미만이면 부정 우세")
    void getNewsBalance_PositiveLessThan30Percent_ReturnsNegativeDominant() {
        // Given
        DinoMaterialResult result = createTestResultWithNews(2, 8); // 20% 긍정

        // When
        String balance = result.getNewsBalance();

        // Then
        assertEquals("부정 우세 (부정 80%)", balance);
    }

    @Test
    @DisplayName("뉴스 밸런스 - 뉴스가 없으면 '뉴스 없음' 반환")
    void getNewsBalance_NoNews_ReturnsNoNews() {
        // Given
        DinoMaterialResult result = createTestResultWithNews(0, 0);

        // When
        String balance = result.getNewsBalance();

        // Then
        assertEquals("뉴스 없음", balance);
    }

    @Test
    @DisplayName("createFailedResult - 실패 결과 생성 검증")
    void createFailedResult_CreatesResultWithZeroScore() {
        // Given
        String stockCode = "005930";

        // When
        DinoMaterialResult failedResult = DinoMaterialResult.createFailedResult(stockCode);

        // Then
        assertEquals(stockCode, failedResult.stockCode());
        assertEquals(stockCode, failedResult.companyName(), "실패 시 회사명은 종목코드로 설정");
        assertEquals(0, failedResult.totalScore(), "실패 시 총점은 0");
        assertEquals(0, failedResult.dividendScore(), "모든 개별 점수는 0");
        assertEquals(0, failedResult.investorSupplyScore());
        assertEquals(0, failedResult.sentimentScore());
        assertEquals(0, failedResult.earningsSurpriseScore());
        assertEquals(0, failedResult.positiveNewsCount());
        assertEquals(0, failedResult.negativeNewsCount());
        assertEquals("분석 실패", failedResult.dividendSignal());
        assertEquals("분석 실패", failedResult.investorSignal());
        assertEquals("분석 실패", failedResult.earningsSignal());
        assertEquals("분석 실패", failedResult.materialStrengthSignal());
        assertNotNull(failedResult.analysisDateTime(), "분석 시점은 설정되어야 함");
        assertNotNull(failedResult.calculationSteps(), "계산 단계 리스트는 null이 아니어야 함");
        assertFalse(failedResult.calculationSteps().isEmpty(), "실패 단계들이 기록되어야 함");
    }

    @Test
    @DisplayName("개별 점수 범위 검증 - 각 지표는 0~1점")
    void individualScores_ShouldBeWithinZeroToOne() {
        // Given & When
        DinoMaterialResult allOne = createTestResult(1, 1, 1, 1, 5);
        DinoMaterialResult allZero = createTestResult(0, 0, 0, 0, 2);

        // Then
        assertTrue(allOne.dividendScore() >= 0 && allOne.dividendScore() <= 1);
        assertTrue(allOne.investorSupplyScore() >= 0 && allOne.investorSupplyScore() <= 1);
        assertTrue(allOne.sentimentScore() >= 0 && allOne.sentimentScore() <= 1);
        assertTrue(allOne.earningsSurpriseScore() >= 0 && allOne.earningsSurpriseScore() <= 1);

        assertTrue(allZero.dividendScore() >= 0 && allZero.dividendScore() <= 1);
        assertTrue(allZero.investorSupplyScore() >= 0 && allZero.investorSupplyScore() <= 1);
        assertTrue(allZero.sentimentScore() >= 0 && allZero.sentimentScore() <= 1);
        assertTrue(allZero.earningsSurpriseScore() >= 0 && allZero.earningsSurpriseScore() <= 1);
    }

    @Test
    @DisplayName("record 불변성 검증 - 모든 필드가 올바르게 생성됨")
    void recordImmutability_AllFieldsCorrectlySet() {
        // Given
        String stockCode = "005930";
        String companyName = "삼성전자";
        int dividendScore = 1;
        int investorSupplyScore = 1;
        int sentimentScore = 0;
        int earningsSurpriseScore = 1;
        int totalScore = 5;

        // When
        DinoMaterialResult result = new DinoMaterialResult(
            stockCode, companyName,
            dividendScore, investorSupplyScore, sentimentScore, earningsSurpriseScore, totalScore,
            5, 2, // positiveNewsCount, negativeNewsCount
            BigDecimal.valueOf(3.5), "기관매집", BigDecimal.valueOf(5.2), "상승",
            BigDecimal.valueOf(65.5), "긍정", BigDecimal.valueOf(15), "고배당",
            "고배당 신호", "기관 매집 중", "긍정 서프라이즈", "강한 재료",
            LocalDateTime.now(),
            new ArrayList<>(),
            "MAX(0, MIN(5, 2 + 3)) = 5점"
        );

        // Then
        assertEquals(stockCode, result.stockCode());
        assertEquals(companyName, result.companyName());
        assertEquals(dividendScore, result.dividendScore());
        assertEquals(investorSupplyScore, result.investorSupplyScore());
        assertEquals(sentimentScore, result.sentimentScore());
        assertEquals(earningsSurpriseScore, result.earningsSurpriseScore());
        assertEquals(totalScore, result.totalScore());
        assertNotNull(result.analysisDateTime());
    }

    /**
     * 테스트용 DinoMaterialResult 생성 헬퍼 메서드 (점수만)
     */
    private DinoMaterialResult createTestResult(
            int dividendScore,
            int investorSupplyScore,
            int sentimentScore,
            int earningsSurpriseScore,
            int totalScore) {

        return new DinoMaterialResult(
            "005930", "삼성전자",
            dividendScore, investorSupplyScore, sentimentScore, earningsSurpriseScore, totalScore,
            5, 2,
            BigDecimal.valueOf(3.5), "기관매집", BigDecimal.valueOf(5.2), "상승",
            BigDecimal.valueOf(65.5), "긍정", BigDecimal.valueOf(15), "고배당",
            "테스트", "테스트", "테스트", "테스트",
            LocalDateTime.now(),
            new ArrayList<>(),
            "테스트"
        );
    }

    /**
     * 테스트용 DinoMaterialResult 생성 헬퍼 메서드 (상세 데이터 포함)
     */
    private DinoMaterialResult createTestResultWithDetails(
            BigDecimal impactScore,
            BigDecimal investorTrend,
            BigDecimal psychologyIndex,
            BigDecimal materialDuration) {

        return new DinoMaterialResult(
            "005930", "삼성전자",
            0, 0, 0, 0, 0,
            5, 2,
            impactScore, "기관매집", investorTrend, "상승",
            psychologyIndex, "긍정", materialDuration, "고배당",
            "테스트", "테스트", "테스트", "테스트",
            LocalDateTime.now(),
            new ArrayList<>(),
            "테스트"
        );
    }

    /**
     * 테스트용 DinoMaterialResult 생성 헬퍼 메서드 (뉴스 데이터 포함)
     */
    private DinoMaterialResult createTestResultWithNews(
            int positiveNewsCount,
            int negativeNewsCount) {

        return new DinoMaterialResult(
            "005930", "삼성전자",
            0, 0, 0, 0, 0,
            positiveNewsCount, negativeNewsCount,
            BigDecimal.valueOf(3.5), "기관매집", BigDecimal.valueOf(5.2), "상승",
            BigDecimal.valueOf(65.5), "긍정", BigDecimal.valueOf(15), "고배당",
            "테스트", "테스트", "테스트", "테스트",
            LocalDateTime.now(),
            new ArrayList<>(),
            "테스트"
        );
    }
}
