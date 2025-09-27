package com.quantum.backtest.domain.strategy;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * 전략 계산 과정 로그를 나타내는 도메인 객체
 * 전략 실행 중 각 계산 단계와 의사결정 과정을 기록
 */
public record StrategyCalculationLog(
        LocalDateTime timestamp,
        LocalDate tradeDay,
        LogType logType,
        String strategyType,
        int stepSequence,
        String description,
        Map<String, Object> inputData,
        Map<String, Object> calculationDetails,
        Map<String, Object> outputResult
) {


    /**
     * 로그 타입 열거형
     */
    public enum LogType {
        CALCULATION("📊", "계산"),      // 수치 계산 과정
        SIGNAL("🎯", "신호"),          // 매매 신호 감지
        DECISION("💭", "판단"),        // 매매 의사결정
        TRADE_EXECUTION("💰", "체결"); // 거래 실행

        private final String icon;
        private final String koreanName;

        LogType(String icon, String koreanName) {
            this.icon = icon;
            this.koreanName = koreanName;
        }

        public String getIcon() {
            return icon;
        }

        public String getKoreanName() {
            return koreanName;
        }
    }

    /**
     * 계산 로그 생성을 위한 팩토리 메서드
     */
    public static StrategyCalculationLog forCalculation(LocalDate tradeDay, String strategyType, int stepSequence,
                                                      String description, Map<String, Object> inputData,
                                                      Map<String, Object> calculationDetails, Map<String, Object> outputResult) {
        return new StrategyCalculationLog(
                LocalDateTime.now(),
                tradeDay,
                LogType.CALCULATION,
                strategyType,
                stepSequence,
                description,
                inputData,
                calculationDetails,
                outputResult
        );
    }

    /**
     * 신호 감지 로그 생성을 위한 팩토리 메서드
     */
    public static StrategyCalculationLog forSignal(LocalDate tradeDay, String strategyType, int stepSequence,
                                                 String description, Map<String, Object> inputData,
                                                 Map<String, Object> signalDetails, Map<String, Object> outputResult) {
        return new StrategyCalculationLog(
                LocalDateTime.now(),
                tradeDay,
                LogType.SIGNAL,
                strategyType,
                stepSequence,
                description,
                inputData,
                signalDetails,
                outputResult
        );
    }

    /**
     * 의사결정 로그 생성을 위한 팩토리 메서드
     */
    public static StrategyCalculationLog forDecision(LocalDate tradeDay, String strategyType, int stepSequence,
                                                   String description, Map<String, Object> inputData,
                                                   Map<String, Object> decisionDetails, Map<String, Object> outputResult) {
        return new StrategyCalculationLog(
                LocalDateTime.now(),
                tradeDay,
                LogType.DECISION,
                strategyType,
                stepSequence,
                description,
                inputData,
                decisionDetails,
                outputResult
        );
    }

    /**
     * 거래 실행 로그 생성을 위한 팩토리 메서드
     */
    public static StrategyCalculationLog forTradeExecution(LocalDate tradeDay, String strategyType, int stepSequence,
                                                         String description, Map<String, Object> inputData,
                                                         Map<String, Object> executionDetails, Map<String, Object> outputResult) {
        return new StrategyCalculationLog(
                LocalDateTime.now(),
                tradeDay,
                LogType.TRADE_EXECUTION,
                strategyType,
                stepSequence,
                description,
                inputData,
                executionDetails,
                outputResult
        );
    }

    /**
     * 입력 데이터의 간단한 문자열 표현 반환
     */
    public String getInputDataAsString() {
        return inputData != null ? inputData.toString() : "{}";
    }

    /**
     * 계산 세부사항의 간단한 문자열 표현 반환
     */
    public String getCalculationDetailsAsString() {
        return calculationDetails != null ? calculationDetails.toString() : "{}";
    }

    /**
     * 출력 결과의 간단한 문자열 표현 반환
     */
    public String getOutputResultAsString() {
        return outputResult != null ? outputResult.toString() : "{}";
    }

    /**
     * 로그의 아이콘 반환
     */
    public String getIcon() {
        return logType.getIcon();
    }

    /**
     * 로그 타입의 한국어 이름 반환
     */
    public String getLogTypeName() {
        return logType.getKoreanName();
    }


    /**
     * 화면 표시를 위한 포맷된 문자열 생성
     */
    public String getFormattedDisplay() {
        return String.format("%s [%s] %s",
            logType.getIcon(),
            logType.getKoreanName(),
            description);
    }
}