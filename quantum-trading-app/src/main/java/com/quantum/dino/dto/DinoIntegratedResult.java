package com.quantum.dino.dto;

import java.time.LocalDateTime;

/**
 * DINO 통합 분석 결과 DTO
 *
 * 4개 영역의 종합 분석 결과를 20점 만점으로 제공
 * - 재무 분석 (5점) + 기술 분석 (5점) + 재료 분석 (5점) + 가격 분석 (5점) = 20점
 *
 * 등급 체계:
 * - S등급: 18-20점 (우수)
 * - A등급: 15-17점 (양호)
 * - B등급: 12-14점 (보통)
 * - C등급: 9-11점 (주의)
 * - D등급: 0-8점 (위험)
 */
public record DinoIntegratedResult(
        // 기본 정보
        String stockCode,
        String companyName,
        LocalDateTime analysisDateTime,

        // 개별 분석 결과 (각 5점 만점)
        DinoFinanceResult financeResult,     // 재무 분석 결과
        DinoTechnicalResult technicalResult, // 기술 분석 결과
        DinoMaterialResult materialResult,   // 재료 분석 결과
        DinoPriceResult priceResult,         // 가격 분석 결과

        // 종합 결과 (20점 만점)
        int totalScore,                      // 0-20점
        String overallGrade,                 // S, A, B, C, D
        String overallSummary,               // 종합 평가 메시지
        String investmentRecommendation      // 투자 권고 사항
) {

    /**
     * 총점을 기준으로 종합 등급을 계산
     */
    public static String calculateOverallGrade(int totalScore) {
        if (totalScore >= 18) return "S";       // 18-20점: 매우 우수
        else if (totalScore >= 15) return "A";  // 15-17점: 우수
        else if (totalScore >= 12) return "B";  // 12-14점: 양호
        else if (totalScore >= 9) return "C";   // 9-11점: 보통
        else return "D";                        // 0-8점: 주의
    }

    /**
     * 총점을 기준으로 종합 평가 메시지 생성
     */
    public static String generateOverallSummary(int totalScore, String grade) {
        return switch (grade) {
            case "S" -> String.format("매우 우수한 투자 기회 (%d점) - 모든 영역에서 높은 점수", totalScore);
            case "A" -> String.format("우수한 투자 기회 (%d점) - 대부분 영역에서 양호한 점수", totalScore);
            case "B" -> String.format("보통 수준의 투자 기회 (%d점) - 일부 영역에서 개선 필요", totalScore);
            case "C" -> String.format("신중한 투자 검토 필요 (%d점) - 여러 영역에서 주의 필요", totalScore);
            case "D" -> String.format("투자 위험 높음 (%d점) - 전반적으로 부정적 지표", totalScore);
            default -> String.format("분석 결과 (%d점)", totalScore);
        };
    }

    /**
     * 등급에 따른 투자 권고 사항 생성
     */
    public static String generateInvestmentRecommendation(String grade, int financeScore, int technicalScore, int materialScore, int priceScore) {
        String baseRecommendation = switch (grade) {
            case "S" -> "적극 매수 추천 - 우수한 기본기와 기술적 강세";
            case "A" -> "매수 고려 - 대부분의 지표가 긍정적";
            case "B" -> "신중한 접근 - 일부 긍정적 요소 존재";
            case "C" -> "관망 권장 - 리스크 요소 점검 필요";
            case "D" -> "투자 주의 - 부정적 지표 다수 확인";
            default -> "추가 분석 필요";
        };

        // 특별한 패턴 감지 및 추가 조언
        StringBuilder recommendation = new StringBuilder(baseRecommendation);

        // 재무는 좋지만 기술적으로 약한 경우
        if (financeScore >= 4 && technicalScore <= 2) {
            recommendation.append(" (기술적 반등 시점 대기 고려)");
        }
        // 기술적으로는 좋지만 재무가 약한 경우
        else if (technicalScore >= 4 && financeScore <= 2) {
            recommendation.append(" (단기 관점, 재무 개선 모니터링 필요)");
        }
        // 재료는 좋지만 다른 지표가 약한 경우
        else if (materialScore >= 4 && (financeScore <= 2 || technicalScore <= 2)) {
            recommendation.append(" (재료주 관점에서 단기 접근)");
        }

        return recommendation.toString();
    }

    /**
     * 총점이 유효한 범위인지 확인 (0~20점)
     */
    public boolean isValidTotalScore() {
        return totalScore >= 0 && totalScore <= 20;
    }

    /**
     * 각 영역별 점수 요약 반환
     */
    public String getScoreBreakdown() {
        return String.format("재무:%d점, 기술:%d점, 재료:%d점, 가격:%d점",
                financeResult != null ? financeResult.totalScore() : 0,
                technicalResult != null ? technicalResult.totalScore() : 0,
                materialResult != null ? materialResult.totalScore() : 0,
                priceResult != null ? priceResult.totalScore() : 0);
    }

    /**
     * 등급에 따른 CSS 클래스 반환 (웹 UI용)
     */
    public String getGradeCssClass() {
        return switch (overallGrade) {
            case "S" -> "grade-s text-success";      // 진한 녹색
            case "A" -> "grade-a text-primary";      // 파란색
            case "B" -> "grade-b text-warning";      // 노란색
            case "C" -> "grade-c text-secondary";    // 회색
            case "D" -> "grade-d text-danger";       // 빨간색
            default -> "grade-unknown text-muted";
        };
    }

    /**
     * 진행률 바를 위한 백분율 반환 (0-100%)
     */
    public int getScorePercentage() {
        return (int) Math.round((totalScore / 20.0) * 100);
    }

    /**
     * 분석 실패 시 기본 결과 생성
     */
    public static DinoIntegratedResult createFailedResult(String stockCode) {
        return new DinoIntegratedResult(
                stockCode,
                stockCode, // 회사명을 종목코드로 대체
                LocalDateTime.now(),
                null, null, null, null, // 모든 개별 결과 null
                0, // 총점 0
                "D", // 최저 등급
                "분석 실패 - 데이터 부족",
                "분석 재시도 권장"
        );
    }

    /**
     * 통합 결과 생성 팩토리 메서드
     */
    public static DinoIntegratedResult create(String stockCode, String companyName,
                                            DinoFinanceResult financeResult,
                                            DinoTechnicalResult technicalResult,
                                            DinoMaterialResult materialResult,
                                            DinoPriceResult priceResult) {

        // 각 영역별 점수 합계 계산
        int financeScore = financeResult != null ? financeResult.totalScore() : 0;
        int technicalScore = technicalResult != null ? technicalResult.totalScore() : 0;
        int materialScore = materialResult != null ? materialResult.totalScore() : 0;
        int priceScore = priceResult != null ? priceResult.totalScore() : 0;

        int totalScore = financeScore + technicalScore + materialScore + priceScore;

        // 등급 및 평가 메시지 생성
        String grade = calculateOverallGrade(totalScore);
        String summary = generateOverallSummary(totalScore, grade);
        String recommendation = generateInvestmentRecommendation(grade, financeScore, technicalScore, materialScore, priceScore);

        return new DinoIntegratedResult(
                stockCode,
                companyName,
                LocalDateTime.now(),
                financeResult,
                technicalResult,
                materialResult,
                priceResult,
                totalScore,
                grade,
                summary,
                recommendation
        );
    }
}