package com.quantum.dino.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.ArrayList;

/**
 * DINO 재료 분석 결과 DTO
 *
 * 재료 분석 5점 만점 구성 (Python 동일 로직):
 * 1. 고배당 (2% 이상) (0~1점)
 * 2. 기관/외국인 수급 (1% 이상 매집) (0~1점)
 * 3. 어닝서프라이즈 (10% 이상) (0~1점) - 향후 구현
 * 4. 기타 소재 항목 - 향후 구현
 *
 * 총점 공식: MAX(0, MIN(5, 2 + SUM(개별점수들)))
 *
 * Python 대응: dino_test/material_analyzer.py의 MaterialScoreDetail
 */
public record DinoMaterialResult(
        String stockCode,
        String companyName,

        // 개별 점수 (Python MaterialScoreDetail와 동일)
        int dividendScore,         // 고배당 점수 (0~1점) - D004
        int investorSupplyScore,   // 기관/외국인 수급 점수 (0~1점) - D003
        int sentimentScore,        // 시장 심리 점수 (0~1점) - 향후 구현
        int earningsSurpriseScore, // 어닝서프라이즈 점수 (0~1점) - D005 향후 구현

        // 총점 (0~5점)
        int totalScore,

        // 분석 상세 데이터 (Python MaterialScoreDetail 매핑)
        int positiveNewsCount,    // 긍정 뉴스 수 (향후 구현)
        int negativeNewsCount,    // 부정 뉴스 수 (향후 구현)
        BigDecimal impactScore,   // 배당 임팩트 점수
        String investorCategory,  // 투자자 수급 카테고리 (기관/외국인/동반매집)
        BigDecimal investorTrend, // 투자자 수급 트렌드
        String sectorTrend,       // 섹터 동향
        BigDecimal psychologyIndex, // 시장 심리 지수 (향후 구현)
        String psychologyState,   // 심리 상태 (향후 구현)
        BigDecimal materialDuration, // 재료 지속성 (향후 구현)
        String dividendType,      // 배당 유형 (고배당/일반)
        String dividendSignal,    // 배당 신호 설명
        String investorSignal,    // 투자자 수급 신호 설명
        String earningsSignal,    // 어닝서프라이즈 신호 설명
        String materialStrengthSignal, // 재료 강도 신호 설명

        LocalDateTime analysisDateTime,

        // 계산 과정 정보 (로깅 및 화면 표시용)
        List<CalculationStep> calculationSteps, // 개별 계산 단계들
        String finalCalculation // 최종 점수 계산 공식 (예: "MAX(0, MIN(5, 2 + (1+1+0))) = 4점")
) {

    /**
     * 총점에 따른 재료 분석 등급 반환
     */
    public String getMaterialGrade() {
        return switch (totalScore) {
            case 5 -> "A+";
            case 4 -> "A";
            case 3 -> "B+";
            case 2 -> "B";
            case 1 -> "C+";
            case 0 -> "C";
            default -> totalScore < 0 ? "D" : "A+";
        };
    }

    /**
     * 재료 분석 종합 설명
     */
    public String getMaterialSummary() {
        if (totalScore >= 4) {
            return "강력한 호재 - 매수 관점에서 매우 긍정적";
        } else if (totalScore >= 2) {
            return "약한 호재 - 긍정적 요소 존재";
        } else if (totalScore >= 0) {
            return "재료 중립 - 특별한 호재/악재 없음";
        } else {
            return "악재 요소 - 주의 깊은 관찰 필요";
        }
    }

    /**
     * 뉴스 밸런스 계산 (긍정/부정 뉴스 비율) - 향후 구현
     */
    public String getNewsBalance() {
        int totalNews = positiveNewsCount + negativeNewsCount;
        if (totalNews == 0) {
            return "뉴스 없음";
        }

        double positiveRatio = (double) positiveNewsCount / totalNews * 100;
        if (positiveRatio >= 70) {
            return String.format("긍정 우세 (%.0f%%)", positiveRatio);
        } else if (positiveRatio >= 30) {
            return String.format("혼재 (긍정 %.0f%%)", positiveRatio);
        } else {
            return String.format("부정 우세 (부정 %.0f%%)", 100 - positiveRatio);
        }
    }

    /**
     * 재료 지속성 평가 - 향후 구현
     */
    public String getMaterialDurability() {
        if (materialDuration == null) {
            return "N/A";
        }

        double days = materialDuration.doubleValue();
        if (days >= 30) {
            return "장기 재료 (30일+)";
        } else if (days >= 7) {
            return String.format("중기 재료 (%.0f일)", days);
        } else {
            return String.format("단기 재료 (%.0f일)", days);
        }
    }

    /**
     * 배당 임팩트를 백분율 문자열로 반환
     */
    public String getFormattedDividendImpact() {
        if (impactScore == null) {
            return "N/A";
        }
        return impactScore.toString() + "%";
    }

    /**
     * 투자자 트렌드를 백분율 문자열로 반환
     */
    public String getFormattedInvestorTrend() {
        if (investorTrend == null) {
            return "N/A";
        }
        String sign = investorTrend.compareTo(BigDecimal.ZERO) >= 0 ? "+" : "";
        return sign + investorTrend.toString() + "%";
    }

    /**
     * 분석 실패 시 기본 결과 생성
     */
    public static DinoMaterialResult createFailedResult(String stockCode) {
        List<CalculationStep> failedSteps = List.of(
                CalculationStep.failure("배당분석", "배당률 분석", "데이터 수집 실패"),
                CalculationStep.failure("수급분석", "기관/외국인 수급 분석", "API 호출 실패"),
                CalculationStep.failure("어닝서프라이즈", "어닝서프라이즈 분석", "데이터 없음")
        );

        return new DinoMaterialResult(
                stockCode, stockCode,
                0, 0, 0, 0, // dividendScore, investorSupplyScore, sentimentScore, earningsSurpriseScore
                0, // totalScore
                0, 0, // positiveNewsCount, negativeNewsCount
                null, "N/A", null, "N/A", // impactScore, investorCategory, investorTrend, sectorTrend
                null, "N/A", null, "N/A", // psychologyIndex, psychologyState, materialDuration, dividendType
                "분석 실패", "분석 실패", "분석 실패", "분석 실패", // dividendSignal, investorSignal, earningsSignal, materialStrengthSignal
                LocalDateTime.now(),
                failedSteps, // calculationSteps
                "분석 실패로 인한 0점 처리" // finalCalculation
        );
    }

    /**
     * 총점이 유효한지 확인 (0~5점 범위)
     */
    public boolean isValidScore() {
        return totalScore >= 0 && totalScore <= 5;
    }

    /**
     * 심리 지수를 문자열로 반환 - 향후 구현
     */
    public String getFormattedPsychologyIndex() {
        if (psychologyIndex == null) {
            return "N/A";
        }
        return psychologyIndex.toString();
    }
}