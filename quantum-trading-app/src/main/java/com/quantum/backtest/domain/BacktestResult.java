package com.quantum.backtest.domain;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

/**
 * 백테스팅 결과 Value Object
 */
public record BacktestResult(
        BigDecimal totalReturn,         // 총 수익률 (%)
        BigDecimal annualizedReturn,    // 연환산 수익률 (%)
        BigDecimal maxDrawdown,         // 최대 손실률 (%)
        int totalTrades,                // 총 거래수
        int winTrades,                  // 수익 거래수
        int lossTrades,                 // 손실 거래수
        BigDecimal winRate,             // 승률 (%)
        BigDecimal sharpeRatio,         // 샤프비율
        BigDecimal finalCapital,        // 최종 자본금
        BigDecimal totalFees            // 총 수수료
) {

    public BacktestResult {
        Objects.requireNonNull(totalReturn, "Total return cannot be null");
        Objects.requireNonNull(annualizedReturn, "Annualized return cannot be null");
        Objects.requireNonNull(maxDrawdown, "Max drawdown cannot be null");
        Objects.requireNonNull(winRate, "Win rate cannot be null");
        Objects.requireNonNull(sharpeRatio, "Sharpe ratio cannot be null");
        Objects.requireNonNull(finalCapital, "Final capital cannot be null");
        Objects.requireNonNull(totalFees, "Total fees cannot be null");

        if (totalTrades < 0) {
            throw new IllegalArgumentException("Total trades cannot be negative");
        }
        if (winTrades < 0 || lossTrades < 0) {
            throw new IllegalArgumentException("Win/Loss trades cannot be negative");
        }
        if (winTrades + lossTrades != totalTrades) {
            throw new IllegalArgumentException("Win trades + Loss trades must equal total trades");
        }
    }

    /**
     * 백테스팅 결과 빌더
     */
    public static class Builder {
        private BigDecimal initialCapital;
        private BigDecimal finalCapital;
        private double periodYears;
        private int totalTrades = 0;
        private int winTrades = 0;
        private int lossTrades = 0;
        private BigDecimal maxDrawdown = BigDecimal.ZERO;
        private BigDecimal totalFees = BigDecimal.ZERO;
        private BigDecimal dailyReturns = BigDecimal.ZERO; // 일일 수익률의 표준편차 계산용

        public Builder initialCapital(BigDecimal initialCapital) {
            this.initialCapital = initialCapital;
            return this;
        }

        public Builder finalCapital(BigDecimal finalCapital) {
            this.finalCapital = finalCapital;
            return this;
        }

        public Builder periodYears(double periodYears) {
            this.periodYears = periodYears;
            return this;
        }

        public Builder totalTrades(int totalTrades) {
            this.totalTrades = totalTrades;
            return this;
        }

        public Builder winTrades(int winTrades) {
            this.winTrades = winTrades;
            return this;
        }

        public Builder lossTrades(int lossTrades) {
            this.lossTrades = lossTrades;
            return this;
        }

        public Builder maxDrawdown(BigDecimal maxDrawdown) {
            this.maxDrawdown = maxDrawdown;
            return this;
        }

        public Builder totalFees(BigDecimal totalFees) {
            this.totalFees = totalFees;
            return this;
        }

        public BacktestResult build() {
            // 총 수익률 계산
            BigDecimal totalReturn = initialCapital.compareTo(BigDecimal.ZERO) > 0
                    ? finalCapital.subtract(initialCapital)
                    .divide(initialCapital, 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100))
                    : BigDecimal.ZERO;

            // 연환산 수익률 계산 (복리)
            BigDecimal annualizedReturn = BigDecimal.ZERO;
            if (periodYears > 0 && finalCapital.compareTo(initialCapital) > 0) {
                double returnRatio = finalCapital.divide(initialCapital, 8, RoundingMode.HALF_UP).doubleValue();
                double annualizedRatio = Math.pow(returnRatio, 1.0 / periodYears);
                annualizedReturn = BigDecimal.valueOf((annualizedRatio - 1.0) * 100)
                        .setScale(4, RoundingMode.HALF_UP);
            }

            // 승률 계산
            BigDecimal winRate = totalTrades > 0
                    ? BigDecimal.valueOf(winTrades).divide(BigDecimal.valueOf(totalTrades), 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100))
                    : BigDecimal.ZERO;

            // 샤프비율 계산 (간단히 수익률/변동성으로 계산, 실제로는 더 복잡함)
            BigDecimal sharpeRatio = BigDecimal.ONE; // 임시값, 실제로는 일일 수익률 데이터 필요

            return new BacktestResult(
                    totalReturn,
                    annualizedReturn,
                    maxDrawdown,
                    totalTrades,
                    winTrades,
                    lossTrades,
                    winRate,
                    sharpeRatio,
                    finalCapital,
                    totalFees
            );
        }
    }

    /**
     * 손익 금액 계산
     */
    public BigDecimal getProfitLoss(BigDecimal initialCapital) {
        return finalCapital.subtract(initialCapital);
    }

    /**
     * 백테스팅이 수익을 낸 경우인지 확인
     */
    public boolean isProfitable() {
        return totalReturn.compareTo(BigDecimal.ZERO) > 0;
    }
}