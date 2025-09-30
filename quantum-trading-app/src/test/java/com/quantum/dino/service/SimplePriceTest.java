package com.quantum.dino.service;

import com.quantum.dino.dto.DinoPriceResult;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

/**
 * 간단한 가격 분석 실제 계산 테스트
 */
@SpringBootTest
@ActiveProfiles("test")
class SimplePriceTest {

    @Autowired
    private DinoPriceService dinoPriceService;

    @Test
    void 삼성전자_가격분석_실제계산() {
        System.out.println("\n========== 삼성전자(005930) 가격 분석 실제 계산 ==========");

        try {
            // 실제 가격 분석 실행
            DinoPriceResult result = dinoPriceService.analyzePriceScore("005930");

            // 결과 출력
            System.out.println("📊 가격 분석 결과:");
            System.out.println("   종목코드: " + result.stockCode());
            System.out.println("   종목명: " + result.companyName());
            System.out.println();

            System.out.println("🎯 점수 상세:");
            System.out.println("   트렌드 점수: " + result.trendScore() + "/2점");
            System.out.println("   모멘텀 점수: " + result.momentumScore() + "/1점");
            System.out.println("   변동성 점수: " + result.volatilityScore() + "/1점");
            System.out.println("   지지/저항 점수: " + result.supportResistanceScore() + "/1점");
            System.out.println("   ─────────────────────");
            System.out.println("   총점: " + result.totalScore() + "/5점");
            System.out.println("   등급: " + result.getPriceGrade());
            System.out.println();

            System.out.println("📈 가격 정보:");
            System.out.println("   현재가: " + result.currentPrice() + "원");
            System.out.println("   가격 변화: " + result.getFormattedPriceChange());
            System.out.println("   변화율: " + result.getFormattedChangeRate());
            System.out.println("   단기 트렌드: " + result.shortTermTrend() + "%");
            System.out.println("   중기 트렌드: " + result.mediumTermTrend() + "%");
            System.out.println("   변동성: " + result.volatility() + "%");
            System.out.println("   지지선: " + result.supportLevel() + "원");
            System.out.println("   저항선: " + result.resistanceLevel() + "원");
            System.out.println();

            System.out.println("💡 신호 분석:");
            System.out.println("   트렌드: " + result.trendSignal());
            System.out.println("   모멘텀: " + result.momentumSignal());
            System.out.println("   변동성: " + result.volatilitySignal());
            System.out.println("   지지/저항: " + result.supportResistanceSignal());
            System.out.println();

            System.out.println("📝 종합 평가:");
            System.out.println("   " + result.getPriceSummary());
            System.out.println();

            System.out.println("⏰ 분석 시각: " + result.analysisDateTime());

            System.out.println("=========================================================\n");

            // 기본 검증
            assert result != null : "분석 결과가 null입니다";
            assert result.stockCode().equals("005930") : "종목코드가 일치하지 않습니다";
            assert result.totalScore() >= 0 && result.totalScore() <= 5 : "총점이 범위를 벗어났습니다: " + result.totalScore();

            System.out.println("✅ 가격 분석 계산 성공!");

        } catch (Exception e) {
            System.err.println("❌ 가격 분석 계산 실패: " + e.getMessage());
            e.printStackTrace();
            throw e;
        }
    }
}