package com.quantum.dino.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * DINO 테스트 재무 분석 결과
 *
 * 재무 영역 5개 지표를 평가하여 0~5점 범위에서 점수를 산출:
 * 1. 매출액 증감 (±1점)
 * 2. 영업이익 상태 (±2점)
 * 3. 영업이익률 (+1점)
 * 4. 유보율 (±1점)
 * 5. 부채비율 (±1점)
 *
 * 최종 점수: MAX(0, MIN(5, 2 + SUM(개별지표점수들)))
 */
public record DinoFinanceResult(
        String stockCode,
        String companyName,

        // 개별 지표 점수
        int revenueGrowthScore,      // 매출액 증감 점수 (±1점)
        int operatingProfitScore,    // 영업이익 상태 점수 (±2점)
        int operatingMarginScore,    // 영업이익률 점수 (+1점)
        int retentionRateScore,      // 유보율 점수 (±1점)
        int debtRatioScore,          // 부채비율 점수 (±1점)

        int totalScore,              // 최종 점수 (0~5점)

        // 상세 계산 결과 (투명성을 위한 실제 수치)
        Double revenueGrowthRate,    // 매출 증가율 (%)
        String operatingProfitTransition, // 영업이익 전환 상태
        Double operatingMarginRate,  // 영업이익률 (%)
        Double retentionRate,        // 유보율 (%)
        Double debtRatio,           // 부채비율 (%)

        // 원본 데이터 (검증용)
        BigDecimal currentRevenue,      // 당년 매출액
        BigDecimal previousRevenue,     // 전년 매출액
        BigDecimal currentOperatingProfit,   // 당년 영업이익
        BigDecimal previousOperatingProfit,  // 전년 영업이익
        BigDecimal totalDebt,          // 총부채
        BigDecimal totalEquity,        // 자기자본
        BigDecimal retainedEarnings,   // 이익잉여금
        BigDecimal capitalStock,       // 자본금

        // 데이터 기준 연월 (YYYYMM 형식)
        String currentPeriod,          // 당년 기준 연월
        String previousPeriod,         // 전년 기준 연월

        LocalDateTime analyzedAt       // 분석 시점
) {
    /**
     * 분석 성공 여부 확인
     */
    public boolean isSuccessful() {
        return currentRevenue != null && previousRevenue != null
            && currentOperatingProfit != null && totalEquity != null;
    }

    /**
     * 분석 등급 산출 (총점 기준)
     */
    public String getGrade() {
        return switch (totalScore) {
            case 5 -> "A+";
            case 4 -> "A";
            case 3 -> "B+";
            case 2 -> "B";
            case 1 -> "C+";
            case 0 -> "C";
            default -> "D";
        };
    }
}