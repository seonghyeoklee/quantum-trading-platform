package com.quantum.dino.service;

import com.quantum.dino.dto.DinoMaterialResult;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

/**
 * 간단한 재료 분석 실제 계산 테스트
 */
@SpringBootTest
@ActiveProfiles("test")
class SimpleMaterialTest {

    @Autowired
    private DinoMaterialService dinoMaterialService;

    @Test
    void 삼성전자_재료분석_실제계산() {
        System.out.println("\n========== 삼성전자(005930) 재료 분석 실제 계산 ==========");

        try {
            // 실제 재료 분석 실행
            DinoMaterialResult result = dinoMaterialService.analyzeMaterialScore("005930");

            // 결과 출력
            System.out.println("📰 재료 분석 결과:");
            System.out.println("   종목코드: " + result.stockCode());
            System.out.println("   종목명: " + result.companyName());
            System.out.println();

            System.out.println("🎯 점수 상세:");
            System.out.println("   배당 점수: " + result.dividendScore() + "/1점");
            System.out.println("   투자자 수급 점수: " + result.investorSupplyScore() + "/1점");
            System.out.println("   시장 심리 점수: " + result.sentimentScore() + "/1점");
            System.out.println("   어닝서프라이즈 점수: " + result.earningsSurpriseScore() + "/1점");
            System.out.println("   ─────────────────────");
            System.out.println("   총점: " + result.totalScore() + "/5점");
            System.out.println("   등급: " + result.getMaterialGrade());
            System.out.println();

            System.out.println("📊 배당 분석:");
            System.out.println("   배당 유형: " + result.dividendType());
            System.out.println("   배당 신호: " + result.dividendSignal());
            System.out.println("   배당 임팩트: " + result.getFormattedDividendImpact());
            System.out.println();

            System.out.println("🏢 투자자 수급 분석:");
            System.out.println("   투자자 카테고리: " + result.investorCategory());
            System.out.println("   투자자 트렌드: " + result.getFormattedInvestorTrend());
            System.out.println("   섹터 트렌드: " + result.sectorTrend());
            System.out.println();

            System.out.println("💭 시장 심리 분석:");
            System.out.println("   심리 지수: " + result.getFormattedPsychologyIndex());
            System.out.println("   심리 상태: " + result.psychologyState());
            System.out.println();

            System.out.println("⚡ 어닝서프라이즈 분석:");
            System.out.println("   어닝서프라이즈 신호: " + result.earningsSignal());
            System.out.println("   재료 지속성: " + result.getMaterialDurability());
            System.out.println();

            System.out.println("💡 신호 분석:");
            System.out.println("   배당 신호: " + result.dividendSignal());
            System.out.println("   투자자 신호: " + result.investorSignal());
            System.out.println("   어닝서프라이즈 신호: " + result.earningsSignal());
            System.out.println("   재료 강도 신호: " + result.materialStrengthSignal());
            System.out.println();

            System.out.println("📝 종합 평가:");
            System.out.println("   " + result.getMaterialSummary());
            System.out.println();

            System.out.println("⏰ 분석 시각: " + result.analysisDateTime());

            System.out.println("=========================================================\n");

            // 기본 검증
            assert result != null : "분석 결과가 null입니다";
            assert result.stockCode().equals("005930") : "종목코드가 일치하지 않습니다";
            assert result.totalScore() >= 0 && result.totalScore() <= 5 : "총점이 범위를 벗어났습니다: " + result.totalScore();
            assert result.isValidScore() : "점수가 유효하지 않습니다";

            System.out.println("✅ 재료 분석 계산 성공!");

        } catch (Exception e) {
            System.err.println("❌ 재료 분석 계산 실패: " + e.getMessage());
            e.printStackTrace();
            throw e;
        }
    }
}