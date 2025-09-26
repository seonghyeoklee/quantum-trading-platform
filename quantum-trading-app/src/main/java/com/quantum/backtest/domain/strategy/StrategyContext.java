package com.quantum.backtest.domain.strategy;

import com.quantum.backtest.domain.Backtest;
import com.quantum.backtest.domain.BacktestConfig;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

/**
 * 전략 실행 컨텍스트
 * 전략 실행에 필요한 모든 컨텍스트 정보를 담는 값 객체
 */
public record StrategyContext(
        BacktestConfig config,
        Backtest backtest,
        BigDecimal initialCapital,
        String stockCode,
        String stockName,
        List<StrategyCalculationLog> calculationLogs
) {

    public static StrategyContext from(Backtest backtest) {
        BacktestConfig config = backtest.getConfig();
        return new StrategyContext(
                config,
                backtest,
                config.initialCapital(),
                config.stockCode(),
                config.stockName(),
                new ArrayList<>() // 계산 로그 리스트 초기화
        );
    }

    /**
     * 백테스팅 진행률 업데이트
     */
    public void updateProgress(int progressPercentage) {
        backtest.updateProgress(progressPercentage);
    }

    /**
     * 거래 추가
     */
    public void addTrade(com.quantum.backtest.domain.Trade trade) {
        backtest.addTrade(trade);
    }

    /**
     * 전략 타입 확인
     */
    public com.quantum.backtest.domain.StrategyType getStrategyType() {
        return config.strategyType();
    }

    /**
     * 백테스팅 기간 (년)
     */
    public double getPeriodYears() {
        return config.getPeriodYears();
    }

    /**
     * 계산 과정 로그 추가
     */
    public void addCalculationLog(StrategyCalculationLog log) {
        calculationLogs.add(log);

        // 로그를 화면에도 출력 (개발 및 디버깅용)
        System.out.println(String.format("[%s] %s - %s",
            log.tradeDay(),
            log.getFormattedDisplay(),
            log.description()));
    }

    /**
     * 모든 계산 로그 조회 (읽기 전용)
     */
    public List<StrategyCalculationLog> getCalculationLogs() {
        return new ArrayList<>(calculationLogs);
    }

    /**
     * 현재 단계 번호 생성 (다음 로그의 sequence number)
     */
    public int getNextStepSequence() {
        return calculationLogs.size() + 1;
    }
}