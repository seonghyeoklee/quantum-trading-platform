package com.quantum.dino.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DINO 분석 계산 과정을 담는 데이터 클래스
 *
 * 각 분석 영역의 계산 단계별 정보를 저장하여
 * 로깅과 화면 표시에 활용
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CalculationStep {

    /**
     * 계산 항목 분류 (예: "배당분석", "수급분석", "매출성장률" 등)
     */
    private String category;

    /**
     * 계산 과정 설명 (예: "배당률 2.5% → 고배당 조건 충족")
     */
    private String description;

    /**
     * 입력값 (원시 데이터)
     */
    private Object inputValue;

    /**
     * 계산 결과값
     */
    private Object outputValue;

    /**
     * 부여된 점수
     */
    private int score;

    /**
     * 점수 부여 이유/기준
     */
    private String reasoning;

    /**
     * 계산 공식 (선택적)
     */
    private String formula;

    /**
     * 단위 정보 (예: "%", "억원", "배" 등)
     */
    private String unit;

    /**
     * 계산 성공 여부
     */
    private boolean success;

    /**
     * 오류 메시지 (실패 시)
     */
    private String errorMessage;

    /**
     * 성공한 계산 단계 생성
     */
    public static CalculationStep success(String category, String description,
                                        Object inputValue, Object outputValue,
                                        int score, String reasoning) {
        CalculationStep step = new CalculationStep();
        step.category = category;
        step.description = description;
        step.inputValue = inputValue;
        step.outputValue = outputValue;
        step.score = score;
        step.reasoning = reasoning;
        step.success = true;
        return step;
    }

    /**
     * 성공한 계산 단계 생성 (공식 포함)
     */
    public static CalculationStep success(String category, String description,
                                        Object inputValue, Object outputValue,
                                        int score, String reasoning, String formula) {
        CalculationStep step = success(category, description, inputValue, outputValue, score, reasoning);
        step.formula = formula;
        return step;
    }

    /**
     * 실패한 계산 단계 생성
     */
    public static CalculationStep failure(String category, String description,
                                        String errorMessage) {
        CalculationStep step = new CalculationStep();
        step.category = category;
        step.description = description;
        step.success = false;
        step.errorMessage = errorMessage;
        step.score = 0;
        return step;
    }

    /**
     * 화면 표시용 포맷된 설명
     */
    public String getFormattedDescription() {
        if (!success) {
            return description + " (실패: " + errorMessage + ")";
        }

        StringBuilder sb = new StringBuilder();
        sb.append(description);

        if (inputValue != null && outputValue != null) {
            sb.append(" (").append(inputValue);
            if (unit != null && !unit.isEmpty()) {
                sb.append(unit);
            }
            sb.append(" → ").append(outputValue);
            if (unit != null && !unit.isEmpty()) {
                sb.append(unit);
            }
            sb.append(")");
        }

        sb.append(" → ").append(score).append("점");

        return sb.toString();
    }

    /**
     * 로깅용 포맷된 설명
     */
    public String getLogDescription() {
        if (!success) {
            return String.format("[%s] %s - 실패: %s", category, description, errorMessage);
        }

        return String.format("[%s] %s → %s점 (%s)",
                           category, description, score, reasoning);
    }
}