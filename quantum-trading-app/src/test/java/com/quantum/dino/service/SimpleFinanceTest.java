package com.quantum.dino.service;

import com.quantum.dino.dto.DinoFinanceResult;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

/**
 * 간단한 재무 분석 실제 계산 테스트
 */
@SpringBootTest
@ActiveProfiles("test")
class SimpleFinanceTest {

    @Autowired
    private DinoFinanceService dinoFinanceService;

    @Test
    void 삼성전자_재무분석_실제계산() {
        System.out.println("\n========== 삼성전자(005930) 재무 분석 실제 계산 ==========");

        try {
            // 실제 재무 분석 실행
            DinoFinanceResult result = dinoFinanceService.analyzeFinanceScore("005930");

            // 결과 출력
            System.out.println("📊 재무 분석 결과:");
            System.out.println("   종목코드: " + result.stockCode());
            System.out.println("   종목명: " + result.companyName());
            System.out.println();

            System.out.println("🎯 점수 상세:");
            System.out.println("   매출액 증감 점수: " + result.revenueGrowthScore() + "점");
            System.out.println("   영업이익 상태 점수: " + result.operatingProfitScore() + "점");
            System.out.println("   영업이익률 점수: " + result.operatingMarginScore() + "점");
            System.out.println("   유보율 점수: " + result.retentionRateScore() + "점");
            System.out.println("   부채비율 점수: " + result.debtRatioScore() + "점");
            System.out.println("   ─────────────────────");
            System.out.println("   총점: " + result.totalScore() + "/5점");
            System.out.println("   등급: " + result.getGrade());
            System.out.println();

            System.out.println("📈 계산 상세:");
            System.out.println("   매출 증가율: " + String.format("%.2f%%", result.revenueGrowthRate()));
            System.out.println("   영업이익 전환: " + result.operatingProfitTransition());
            System.out.println("   영업이익률: " + String.format("%.2f%%", result.operatingMarginRate()));
            System.out.println("   유보율: " + String.format("%.2f%%", result.retentionRate()));
            System.out.println("   부채비율: " + String.format("%.2f%%", result.debtRatio()));
            System.out.println();

            System.out.println("💰 원본 데이터:");
            System.out.println("   당년 매출액: " + String.format("%,.0f원", result.currentRevenue()));
            System.out.println("   전년 매출액: " + String.format("%,.0f원", result.previousRevenue()));
            System.out.println("   당년 영업이익: " + String.format("%,.0f원", result.currentOperatingProfit()));
            System.out.println("   전년 영업이익: " + String.format("%,.0f원", result.previousOperatingProfit()));
            System.out.println("   총부채: " + String.format("%,.0f원", result.totalDebt()));
            System.out.println("   자기자본: " + String.format("%,.0f원", result.totalEquity()));
            System.out.println("   이익잉여금: " + String.format("%,.0f원", result.retainedEarnings()));
            System.out.println("   자본금: " + String.format("%,.0f원", result.capitalStock()));
            System.out.println();

            System.out.println("📅 분석 기준:");
            System.out.println("   당년 기준: " + result.currentPeriod());
            System.out.println("   전년 기준: " + result.previousPeriod());
            System.out.println("   분석 시각: " + result.analyzedAt());

            System.out.println("=========================================================\n");

            // 기본 검증
            assert result != null : "분석 결과가 null입니다";
            assert result.stockCode().equals("005930") : "종목코드가 일치하지 않습니다";
            assert result.totalScore() >= 0 && result.totalScore() <= 5 : "총점이 범위를 벗어났습니다: " + result.totalScore();

            // 수동 계산 검증
            System.out.println("✅ 수동 계산 검증:");

            // 1. 매출액 증가율 검증 (8.08% -> 0점)
            double expectedRevenueGrowth = 8.08;
            double actualRevenueGrowth = result.revenueGrowthRate();
            System.out.println("   매출 증가율: 예상 " + expectedRevenueGrowth + "%, 실제 " + String.format("%.2f%%", actualRevenueGrowth));
            assert Math.abs(actualRevenueGrowth - expectedRevenueGrowth) < 0.1 : "매출 증가율 계산 오류";
            assert result.revenueGrowthScore() == 0 : "매출액 점수가 0점이어야 합니다";

            // 2. 영업이익률 검증 (17.98% -> 1점)
            double expectedOperatingMargin = 17.98;
            double actualOperatingMargin = result.operatingMarginRate();
            System.out.println("   영업이익률: 예상 " + expectedOperatingMargin + "%, 실제 " + String.format("%.2f%%", actualOperatingMargin));
            assert Math.abs(actualOperatingMargin - expectedOperatingMargin) < 0.1 : "영업이익률 계산 오류";
            assert result.operatingMarginScore() == 1 : "영업이익률 점수가 1점이어야 합니다";

            // 3. 유보율 검증 (2310% -> 1점)
            double expectedRetentionRate = 2310.1;
            double actualRetentionRate = result.retentionRate();
            System.out.println("   유보율: 예상 " + expectedRetentionRate + "%, 실제 " + String.format("%.2f%%", actualRetentionRate));
            assert Math.abs(actualRetentionRate - expectedRetentionRate) < 10 : "유보율 계산 오류";
            assert result.retentionRateScore() == 1 : "유보율 점수가 1점이어야 합니다";

            // 4. 부채비율 검증 (24.7% -> 1점)
            double expectedDebtRatio = 24.7;
            double actualDebtRatio = result.debtRatio();
            System.out.println("   부채비율: 예상 " + expectedDebtRatio + "%, 실제 " + String.format("%.2f%%", actualDebtRatio));
            assert Math.abs(actualDebtRatio - expectedDebtRatio) < 0.1 : "부채비율 계산 오류";
            assert result.debtRatioScore() == 1 : "부채비율 점수가 1점이어야 합니다";

            // 5. 최종 점수 검증 (0 + 0 + 1 + 1 + 1 = 3, MAX(0, MIN(5, 2 + 3)) = 5점)
            int expectedIndividualSum = 0 + 0 + 1 + 1 + 1;
            int expectedTotalScore = Math.max(0, Math.min(5, 2 + expectedIndividualSum));
            System.out.println("   개별 점수 합계: " + expectedIndividualSum + "점");
            System.out.println("   최종 점수: 예상 " + expectedTotalScore + "점, 실제 " + result.totalScore() + "점");
            assert result.totalScore() == expectedTotalScore : "최종 점수 계산 오류";

            System.out.println("\n✅ 재무 분석 계산 성공! 모든 검증 통과!");

        } catch (Exception e) {
            System.err.println("❌ 재무 분석 계산 실패: " + e.getMessage());
            e.printStackTrace();
            throw e;
        }
    }
}