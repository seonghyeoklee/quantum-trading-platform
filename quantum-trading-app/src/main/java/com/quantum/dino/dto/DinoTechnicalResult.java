package com.quantum.dino.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * DINO 기술 분석 결과 DTO
 *
 * 기술 분석 영역 5점 만점 구성 (Python 로직과 일치):
 * - OBV 분석 (±1점): 2년 변화율과 주가 추세 일치도
 * - RSI 상태 분석 (±1점): 14일 RSI 과매수/과매도 상태
 * - 투자심리 분석 (±1점): Stochastic Oscillator 기반
 * - 기타지표 분석 (±1점): MACD 기반
 *
 * 최종 점수 공식: MAX(0, MIN(5, 2 + SUM(4개 지표)))
 */
public record DinoTechnicalResult(
        String stockCode,
        String companyName,

        // 개별 점수 (Python 로직과 동일한 4개 지표 각 ±1점)
        int obvScore,             // OBV 점수 (-1 ~ +1점)
        int rsiScore,             // RSI 점수 (-1 ~ +1점)
        int stochasticScore,      // Stochastic 점수 (-1 ~ +1점)
        int macdScore,            // MACD 점수 (-1 ~ +1점)

        // 총점 (0~5점)
        int totalScore,

        // 분석 상세 데이터
        BigDecimal obvValue,          // 현재 OBV 값
        BigDecimal currentRSI,        // 현재 RSI 값
        BigDecimal stochasticValue,   // 현재 Stochastic 값
        BigDecimal macdValue,         // 현재 MACD 값
        String obvSignal,             // OBV 신호 설명
        String rsiSignal,             // RSI 신호 설명
        String stochasticSignal,      // Stochastic 신호 설명
        String macdSignal,            // MACD 신호 설명

        LocalDateTime analysisDateTime
) {

    /**
     * 총점에 따른 기술 분석 등급 반환
     */
    public String getTechnicalGrade() {
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
     * 기술 분석 종합 설명
     */
    public String getTechnicalSummary() {
        if (totalScore >= 4) {
            return "강한 상승 신호 - 매수 관점에서 긍정적";
        } else if (totalScore >= 2) {
            return "약한 상승 신호 - 관망 후 진입 고려";
        } else if (totalScore >= 0) {
            return "중립 상태 - 추가 신호 확인 필요";
        } else {
            return "약세 신호 - 하락 리스크 주의";
        }
    }

    /**
     * 분석 실패 시 기본 결과 생성
     * 분석 실패 시에는 모든 점수를 0으로 설정
     */
    public static DinoTechnicalResult createFailedResult(String stockCode, String companyName) {
        return new DinoTechnicalResult(
                stockCode, companyName, 0, 0, 0, 0, 0,  // 분석 실패 시 총점 0
                null, null, null, null,
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
}