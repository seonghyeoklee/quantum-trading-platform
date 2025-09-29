package com.quantum.dino.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * DINO 가격 분석 결과 DTO
 *
 * 가격 분석 영역 5점 만점 구성:
 * - 가격 트렌드 분석 (2점): 단기/중기 가격 추세 분석
 * - 모멘텀 분석 (1점): 가격 변화율 및 가속도 분석
 * - 변동성 분석 (1점): 가격 안정성 및 리스크 평가
 * - 지지/저항선 분석 (1점): 주요 가격 레벨 돌파/지지 상황
 */
public record DinoPriceResult(
        String stockCode,
        String companyName,

        // 개별 점수 (각 항목별 상세 점수)
        int trendScore,           // 가격 트렌드 점수 (-2 ~ +2점)
        int momentumScore,        // 모멘텀 점수 (-1 ~ +1점)
        int volatilityScore,      // 변동성 점수 (-1 ~ +1점)
        int supportResistanceScore, // 지지/저항선 점수 (-1 ~ +1점)

        // 총점 (0~5점)
        int totalScore,

        // 분석 상세 데이터
        BigDecimal currentPrice,         // 현재가
        BigDecimal priceChange,          // 가격 변화액
        BigDecimal priceChangeRate,      // 가격 변화율 (%)
        BigDecimal shortTermTrend,       // 단기 트렌드 (5일 평균 변화율)
        BigDecimal mediumTermTrend,      // 중기 트렌드 (20일 평균 변화율)
        BigDecimal volatility,           // 변동성 (20일 표준편차)
        BigDecimal supportLevel,         // 지지선 수준
        BigDecimal resistanceLevel,      // 저항선 수준
        String trendSignal,              // 트렌드 신호 설명
        String momentumSignal,           // 모멘텀 신호 설명
        String volatilitySignal,         // 변동성 신호 설명
        String supportResistanceSignal,  // 지지/저항선 신호 설명

        LocalDateTime analysisDateTime
) {

    /**
     * 총점에 따른 가격 분석 등급 반환
     */
    public String getPriceGrade() {
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
     * 가격 분석 종합 설명
     */
    public String getPriceSummary() {
        if (totalScore >= 4) {
            return "강한 가격 상승 신호 - 매수 관점에서 긍정적";
        } else if (totalScore >= 2) {
            return "약한 가격 상승 신호 - 신중한 접근 권장";
        } else if (totalScore >= 0) {
            return "가격 중립 상태 - 추가 모니터링 필요";
        } else {
            return "가격 하락 신호 - 리스크 관리 필요";
        }
    }

    /**
     * 분석 실패 시 기본 결과 생성
     */
    public static DinoPriceResult createFailedResult(String stockCode) {
        return new DinoPriceResult(
                stockCode, stockCode, 0, 0, 0, 0, 0,
                null, null, null, null, null, null, null, null,
                "분석 실패", "분석 실패", "분석 실패", "분석 실패",
                LocalDateTime.now()
        );
    }

    /**
     * 총점이 유효한지 확인 (0~5점 범위)
     */
    public boolean isValidScore() {
        return totalScore >= 0 && totalScore <= 5;
    }

    /**
     * 가격 변화율을 백분율 문자열로 반환
     */
    public String getFormattedChangeRate() {
        if (priceChangeRate == null) {
            return "N/A";
        }
        String sign = priceChangeRate.compareTo(BigDecimal.ZERO) >= 0 ? "+" : "";
        return sign + priceChangeRate.toString() + "%";
    }

    /**
     * 가격 변화액을 원화 형식으로 반환
     */
    public String getFormattedPriceChange() {
        if (priceChange == null) {
            return "N/A";
        }
        String sign = priceChange.compareTo(BigDecimal.ZERO) >= 0 ? "+" : "";
        return sign + priceChange.toString() + "원";
    }
}