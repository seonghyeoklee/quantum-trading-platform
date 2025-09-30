package com.quantum.dino.service;

import com.quantum.dino.dto.DinoTechnicalResult;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.junit.jupiter.api.Assertions.*;

/**
 * DinoTechnicalService 테스트
 *
 * 기술 분석 5점 시스템 검증 (Python 로직과 일치):
 * - OBV 분석: ±1점 (2년 변화율과 주가 추세 일치도)
 * - RSI 상태 분석: ±1점 (14일 RSI 과매수/과매도 상태)
 * - Stochastic 분석: ±1점 (투자심리 분석)
 * - MACD 분석: ±1점 (기타지표 분석)
 * - 총점: MAX(0, MIN(5, 2 + SUM(개별점수들)))
 */
@SpringBootTest
@ActiveProfiles("test")
class DinoTechnicalServiceTest {

    @Autowired
    private DinoTechnicalService dinoTechnicalService;

    @Test
    void testAnalyzeTechnicalScore_삼성전자_샘플데이터() {
        // When
        DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

        // Then
        assertNotNull(result, "기술 분석 결과가 null이면 안됩니다");
        assertEquals("005930", result.stockCode());
        assertEquals("삼성전자", result.companyName());

        // 점수 범위 검증 (Python 로직과 동일한 4개 지표 각 ±1점)
        assertTrue(result.obvScore() >= -1 && result.obvScore() <= 1,
                  "OBV 점수는 -1~1 범위여야 합니다: " + result.obvScore());
        assertTrue(result.rsiScore() >= -1 && result.rsiScore() <= 1,
                  "RSI 점수는 -1~1 범위여야 합니다: " + result.rsiScore());
        assertTrue(result.stochasticScore() >= -1 && result.stochasticScore() <= 1,
                  "Stochastic 점수는 -1~1 범위여야 합니다: " + result.stochasticScore());
        assertTrue(result.macdScore() >= -1 && result.macdScore() <= 1,
                  "MACD 점수는 -1~1 범위여야 합니다: " + result.macdScore());
        assertTrue(result.totalScore() >= 0 && result.totalScore() <= 5,
                  "총점은 0~5 범위여야 합니다: " + result.totalScore());

        // 기술 분석 데이터 검증
        assertNotNull(result.obvValue(), "OBV 값이 null이면 안됩니다");
        assertNotNull(result.currentRSI(), "RSI 값이 null이면 안됩니다");
        assertNotNull(result.stochasticValue(), "Stochastic 값이 null이면 안됩니다");
        assertNotNull(result.macdValue(), "MACD 값이 null이면 안됩니다");

        // 신호 메시지 검증
        assertNotNull(result.obvSignal(), "OBV 신호가 null이면 안됩니다");
        assertNotNull(result.rsiSignal(), "RSI 신호가 null이면 안됩니다");
        assertNotNull(result.stochasticSignal(), "Stochastic 신호가 null이면 안됩니다");
        assertNotNull(result.macdSignal(), "MACD 신호가 null이면 안됩니다");

        // 등급 검증
        assertNotNull(result.getTechnicalGrade(), "기술 분석 등급이 null이면 안됩니다");
        assertTrue(result.getTechnicalGrade().matches("[A-D][+]?"),
                  "등급 형식이 올바르지 않습니다: " + result.getTechnicalGrade());

        // 분석 시간 검증
        assertNotNull(result.analysisDateTime(), "분석 시간이 null이면 안됩니다");

        // 결과 출력 (디버깅용)
        System.out.println("=== 삼성전자(005930) 기술 분석 결과 (Python 로직) ===");
        System.out.println("OBV 점수: " + result.obvScore() + "점 (" + result.obvSignal() + ")");
        System.out.println("RSI 점수: " + result.rsiScore() + "점 (" + result.rsiSignal() + ")");
        System.out.println("Stochastic 점수: " + result.stochasticScore() + "점 (" + result.stochasticSignal() + ")");
        System.out.println("MACD 점수: " + result.macdScore() + "점 (" + result.macdSignal() + ")");
        System.out.println("총점: " + result.totalScore() + "/5점 (등급: " + result.getTechnicalGrade() + ")");
        System.out.println("종합 평가: " + result.getTechnicalSummary());
        System.out.println();
        System.out.println("기술 지표 값:");
        System.out.println("- OBV: " + result.obvValue());
        System.out.println("- RSI(14): " + result.currentRSI());
        System.out.println("- Stochastic: " + result.stochasticValue());
        System.out.println("- MACD: " + result.macdValue());

        // 점수 공식 검증
        int individualSum = result.obvScore() + result.rsiScore() + result.stochasticScore() + result.macdScore();
        int expectedTotalScore = Math.max(0, Math.min(5, 2 + individualSum));
        System.out.println();
        System.out.println("점수 공식 검증:");
        System.out.println("개별 점수 합계: " + individualSum + "점");
        System.out.println("예상 총점: " + expectedTotalScore + "점");
        System.out.println("실제 총점: " + result.totalScore() + "점");
        assertEquals(expectedTotalScore, result.totalScore(), "총점 계산 공식이 일치하지 않습니다");
    }

    @Test
    void testGetTechnicalGrade_점수별_등급() {
        // Given & When & Then
        assertEquals("A+", createResult(5).getTechnicalGrade());
        assertEquals("A", createResult(4).getTechnicalGrade());
        assertEquals("B+", createResult(3).getTechnicalGrade());
        assertEquals("B", createResult(2).getTechnicalGrade());
        assertEquals("C+", createResult(1).getTechnicalGrade());
        assertEquals("C", createResult(0).getTechnicalGrade());
        assertEquals("D", createResult(-1).getTechnicalGrade());
    }

    @Test
    void testGetTechnicalSummary_점수별_요약() {
        // 강한 상승 신호
        DinoTechnicalResult strongBuy = createResult(5);
        assertTrue(strongBuy.getTechnicalSummary().contains("강한 상승 신호"));

        // 약한 상승 신호
        DinoTechnicalResult weakBuy = createResult(3);
        assertTrue(weakBuy.getTechnicalSummary().contains("약한 상승 신호"));

        // 중립 상태
        DinoTechnicalResult neutral = createResult(1);
        assertTrue(neutral.getTechnicalSummary().contains("중립 상태"));

        // 약세 신호
        DinoTechnicalResult bearish = createResult(-1);
        assertTrue(bearish.getTechnicalSummary().contains("약세 신호"));
    }

    @Test
    void testCreateFailedResult() {
        // When
        DinoTechnicalResult failedResult = DinoTechnicalResult.createFailedResult("000000", "000000");

        // Then
        assertEquals("000000", failedResult.stockCode());
        assertEquals("000000", failedResult.companyName());
        assertEquals(0, failedResult.totalScore());
        assertEquals("분석 실패", failedResult.obvSignal());
        assertEquals("분석 실패", failedResult.rsiSignal());
        assertEquals("분석 실패", failedResult.stochasticSignal());
        assertEquals("분석 실패", failedResult.macdSignal());
        assertNotNull(failedResult.analysisDateTime());
    }

    @Test
    void testIsValidScore() {
        // Valid scores
        assertTrue(createResult(0).isValidScore());
        assertTrue(createResult(3).isValidScore());
        assertTrue(createResult(5).isValidScore());

        // Invalid scores (would be invalid if we allowed them)
        assertFalse(createResult(-1).isValidScore());
        assertFalse(createResult(6).isValidScore());
    }

    /**
     * 테스트용 DinoTechnicalResult 생성 헬퍼 (새로운 4개 지표 시스템)
     */
    private DinoTechnicalResult createResult(int totalScore) {
        return new DinoTechnicalResult(
            "TEST", "테스트종목",
            0, 0, 0, 0, totalScore,  // obvScore, rsiScore, stochasticScore, macdScore, totalScore
            null, null, null, null,  // obvValue, currentRSI, stochasticValue, macdValue
            "테스트", "테스트", "테스트", "테스트",  // obvSignal, rsiSignal, stochasticSignal, macdSignal
            java.time.LocalDateTime.now()
        );
    }
}