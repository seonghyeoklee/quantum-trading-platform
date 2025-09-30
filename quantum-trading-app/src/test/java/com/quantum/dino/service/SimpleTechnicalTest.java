package com.quantum.dino.service;

import com.quantum.dino.dto.DinoTechnicalResult;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

/**
 * 간단한 기술 분석 실제 계산 테스트
 */
@SpringBootTest
@ActiveProfiles("test")
class SimpleTechnicalTest {

    @Autowired
    private DinoTechnicalService dinoTechnicalService;

    @Test
    void 삼성전자_기술분석_실제계산() {
        System.out.println("\n========== 삼성전자(005930) 기술 분석 실제 계산 ==========");

        try {
            // 실제 기술 분석 실행
            DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore("005930");

            // 결과 출력
            System.out.println("📊 기술 분석 결과:");
            System.out.println("   종목코드: " + result.stockCode());
            System.out.println("   종목명: " + result.companyName());
            System.out.println();

            System.out.println("🎯 점수 상세:");
            System.out.println("   OBV 점수: " + result.obvScore() + "/±1점");
            System.out.println("   RSI 점수: " + result.rsiScore() + "/±1점");
            System.out.println("   Stochastic 점수: " + result.stochasticScore() + "/±1점");
            System.out.println("   MACD 점수: " + result.macdScore() + "/±1점");
            System.out.println("   ─────────────────────");
            System.out.println("   총점: " + result.totalScore() + "/5점");
            System.out.println("   등급: " + result.getTechnicalGrade());
            System.out.println();

            System.out.println("📊 지표 값:");
            System.out.println("   OBV 값: " + (result.obvValue() != null ? String.format("%.2f", result.obvValue()) : "계산 실패"));
            System.out.println("   RSI 값: " + (result.currentRSI() != null ? String.format("%.2f", result.currentRSI()) : "계산 실패"));
            System.out.println("   Stochastic 값: " + (result.stochasticValue() != null ? String.format("%.2f", result.stochasticValue()) : "계산 실패"));
            System.out.println("   MACD 값: " + (result.macdValue() != null ? String.format("%.4f", result.macdValue()) : "계산 실패"));
            System.out.println();

            System.out.println("💡 신호 분석:");
            System.out.println("   OBV 신호: " + result.obvSignal());
            System.out.println("   RSI 신호: " + result.rsiSignal());
            System.out.println("   Stochastic 신호: " + result.stochasticSignal());
            System.out.println("   MACD 신호: " + result.macdSignal());
            System.out.println();

            System.out.println("📝 종합 평가:");
            System.out.println("   " + result.getTechnicalSummary());
            System.out.println();

            System.out.println("⏰ 분석 시각: " + result.analysisDateTime());

            System.out.println("=========================================================\n");

            // 기본 검증
            assert result != null : "분석 결과가 null입니다";
            assert result.stockCode().equals("005930") : "종목코드가 일치하지 않습니다";
            assert result.totalScore() >= 0 && result.totalScore() <= 5 : "총점이 범위를 벗어났습니다: " + result.totalScore();
            assert result.isValidScore() : "점수가 유효하지 않습니다";

            // 개별 점수 범위 검증 (Python 로직에 따라 각 지표 ±1점)
            assert result.obvScore() >= -1 && result.obvScore() <= 1 : "OBV 점수가 범위를 벗어났습니다: " + result.obvScore();
            assert result.rsiScore() >= -1 && result.rsiScore() <= 1 : "RSI 점수가 범위를 벗어났습니다: " + result.rsiScore();
            assert result.stochasticScore() >= -1 && result.stochasticScore() <= 1 : "Stochastic 점수가 범위를 벗어났습니다: " + result.stochasticScore();
            assert result.macdScore() >= -1 && result.macdScore() <= 1 : "MACD 점수가 범위를 벗어났습니다: " + result.macdScore();

            // 점수 공식 검증: MAX(0, MIN(5, 2 + SUM(개별점수들)))
            int individualSum = result.obvScore() + result.rsiScore() + result.stochasticScore() + result.macdScore();
            int expectedTotalScore = Math.max(0, Math.min(5, 2 + individualSum));
            System.out.println("✅ 점수 공식 검증:");
            System.out.println("   개별 점수 합계: " + individualSum + "점");
            System.out.println("   예상 총점: " + expectedTotalScore + "점");
            System.out.println("   실제 총점: " + result.totalScore() + "점");
            assert result.totalScore() == expectedTotalScore : "총점 계산 공식이 일치하지 않습니다";

            System.out.println("\n✅ 기술 분석 계산 성공! 모든 검증 통과!");

        } catch (Exception e) {
            System.err.println("❌ 기술 분석 계산 실패: " + e.getMessage());
            e.printStackTrace();
            throw e;
        }
    }
}