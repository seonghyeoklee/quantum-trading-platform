package com.quantum.backtest.domain.strategy.util;

import com.quantum.backtest.domain.PriceData;
import com.quantum.backtest.domain.strategy.StrategyCalculationLog;
import com.quantum.backtest.domain.strategy.StrategyContext;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * RSI(Relative Strength Index) 계산 유틸리티
 * - 14일 기간의 RSI를 계산 (표준 설정)
 * - Wilder's Smoothing 방식 사용
 * - 과매수/과매도 임계값: 70/30
 */
public class RSICalculator {

    public static final int DEFAULT_RSI_PERIOD = 14;
    public static final double OVERSOLD_THRESHOLD = 30.0;
    public static final double OVERBOUGHT_THRESHOLD = 70.0;

    /**
     * RSI 신호 타입
     */
    public enum RSISignal {
        OVERSOLD,    // 과매도 (30 미만)
        OVERBOUGHT,  // 과매수 (70 초과)
        NEUTRAL      // 중립 (30-70)
    }

    /**
     * RSI 값을 계산하고 로깅과 함께 반환
     *
     * @param context StrategyContext (로깅용)
     * @param priceHistory 가격 데이터 리스트
     * @param period RSI 계산 기간 (기본 14일)
     * @param displayName 표시용 이름 (로깅용)
     * @return RSI 값 리스트 (첫 period개는 null)
     */
    public static List<BigDecimal> calculateRSIWithLogging(StrategyContext context,
                                                           List<PriceData> priceHistory,
                                                           int period,
                                                           String displayName) {
        List<BigDecimal> rsiValues = new ArrayList<>();

        // 첫 period개는 null로 초기화
        for (int i = 0; i < period; i++) {
            rsiValues.add(null);
        }

        if (priceHistory.size() <= period) {
            return rsiValues;
        }

        // 첫 번째 RS와 RSI 계산
        BigDecimal firstAvgGain = BigDecimal.ZERO;
        BigDecimal firstAvgLoss = BigDecimal.ZERO;

        for (int i = 1; i <= period; i++) {
            BigDecimal change = priceHistory.get(i).close().subtract(priceHistory.get(i - 1).close());
            if (change.compareTo(BigDecimal.ZERO) > 0) {
                firstAvgGain = firstAvgGain.add(change);
            } else {
                firstAvgLoss = firstAvgLoss.add(change.abs());
            }
        }

        firstAvgGain = firstAvgGain.divide(BigDecimal.valueOf(period), 6, RoundingMode.HALF_UP);
        firstAvgLoss = firstAvgLoss.divide(BigDecimal.valueOf(period), 6, RoundingMode.HALF_UP);

        // 첫 번째 RSI 계산 및 로깅
        BigDecimal firstRSI = calculateRSI(firstAvgGain, firstAvgLoss);
        rsiValues.add(firstRSI);

        logRSICalculation(context, priceHistory.get(period), period, firstRSI,
                         firstAvgGain, firstAvgLoss, displayName, true);

        // 이후 RSI 계산 (Wilder's Smoothing)
        BigDecimal avgGain = firstAvgGain;
        BigDecimal avgLoss = firstAvgLoss;

        for (int i = period + 1; i < priceHistory.size(); i++) {
            BigDecimal change = priceHistory.get(i).close().subtract(priceHistory.get(i - 1).close());
            BigDecimal currentGain = change.compareTo(BigDecimal.ZERO) > 0 ? change : BigDecimal.ZERO;
            BigDecimal currentLoss = change.compareTo(BigDecimal.ZERO) < 0 ? change.abs() : BigDecimal.ZERO;

            // Wilder's Smoothing
            avgGain = avgGain.multiply(BigDecimal.valueOf(period - 1))
                           .add(currentGain)
                           .divide(BigDecimal.valueOf(period), 6, RoundingMode.HALF_UP);

            avgLoss = avgLoss.multiply(BigDecimal.valueOf(period - 1))
                           .add(currentLoss)
                           .divide(BigDecimal.valueOf(period), 6, RoundingMode.HALF_UP);

            BigDecimal rsi = calculateRSI(avgGain, avgLoss);
            rsiValues.add(rsi);

            // 주요 신호 발생 시점만 로깅 (과매수/과매도)
            RSISignal signal = determineRSISignal(rsi);
            if (signal != RSISignal.NEUTRAL) {
                logRSICalculation(context, priceHistory.get(i), period, rsi,
                                 avgGain, avgLoss, displayName, false);
            }
        }

        return rsiValues;
    }

    /**
     * RSI 값 계산
     */
    private static BigDecimal calculateRSI(BigDecimal avgGain, BigDecimal avgLoss) {
        if (avgLoss.compareTo(BigDecimal.ZERO) == 0) {
            return BigDecimal.valueOf(100);
        }

        BigDecimal rs = avgGain.divide(avgLoss, 6, RoundingMode.HALF_UP);
        BigDecimal rsi = BigDecimal.valueOf(100).subtract(
            BigDecimal.valueOf(100).divide(
                BigDecimal.ONE.add(rs), 2, RoundingMode.HALF_UP
            )
        );

        return rsi;
    }

    /**
     * RSI 신호 판단
     */
    public static RSISignal determineRSISignal(BigDecimal rsi) {
        if (rsi == null) return RSISignal.NEUTRAL;

        double rsiValue = rsi.doubleValue();
        if (rsiValue < OVERSOLD_THRESHOLD) {
            return RSISignal.OVERSOLD;
        } else if (rsiValue > OVERBOUGHT_THRESHOLD) {
            return RSISignal.OVERBOUGHT;
        } else {
            return RSISignal.NEUTRAL;
        }
    }

    /**
     * RSI 계산 과정 로깅
     */
    private static void logRSICalculation(StrategyContext context, PriceData currentDay,
                                         int period, BigDecimal rsi,
                                         BigDecimal avgGain, BigDecimal avgLoss,
                                         String displayName, boolean isFirst) {
        RSISignal signal = determineRSISignal(rsi);
        String signalText = getSignalText(signal);

        Map<String, Object> inputData = new HashMap<>();
        inputData.put("date", currentDay.date().toString());
        inputData.put("price", currentDay.close().toString());
        inputData.put("period", period);
        inputData.put("displayName", displayName);

        Map<String, Object> calculationDetails = new HashMap<>();
        calculationDetails.put("avgGain", avgGain.toString());
        calculationDetails.put("avgLoss", avgLoss.toString());
        calculationDetails.put("method", isFirst ? "초기계산" : "Wilder's Smoothing");
        calculationDetails.put("formula", "RSI = 100 - (100 / (1 + RS)), RS = 평균상승/평균하락");

        Map<String, Object> outputResult = new HashMap<>();
        outputResult.put("rsi", rsi.toString());
        outputResult.put("signal", signal.name());
        outputResult.put("signalText", signalText);
        outputResult.put("isOversold", signal == RSISignal.OVERSOLD);
        outputResult.put("isOverbought", signal == RSISignal.OVERBOUGHT);

        String description = String.format("%s RSI 계산: %.2f (%s)",
                                         displayName, rsi, signalText);

        StrategyCalculationLog log = StrategyCalculationLog.forCalculation(
                currentDay.date(),
                context.getStrategyType().name(),
                context.getNextStepSequence(),
                description,
                inputData,
                calculationDetails,
                outputResult
        );

        context.addCalculationLog(log);
    }

    /**
     * RSI 신호 텍스트 반환
     */
    private static String getSignalText(RSISignal signal) {
        return switch (signal) {
            case OVERSOLD -> "과매도";
            case OVERBOUGHT -> "과매수";
            case NEUTRAL -> "중립";
        };
    }

    /**
     * 현재 RSI가 매수 조건인지 확인
     * (과매도 탈출: RSI > 30 && RSI < 70)
     */
    public static boolean isBuyCondition(BigDecimal rsi) {
        if (rsi == null) return false;
        double value = rsi.doubleValue();
        return value > OVERSOLD_THRESHOLD && value < OVERBOUGHT_THRESHOLD;
    }

    /**
     * 현재 RSI가 매도 조건인지 확인
     * (과매수: RSI > 70)
     */
    public static boolean isSellCondition(BigDecimal rsi) {
        if (rsi == null) return false;
        return rsi.doubleValue() > OVERBOUGHT_THRESHOLD;
    }

    /**
     * RSI 강제 매도 조건 확인 (RSI > 75)
     */
    public static boolean isStrongSellCondition(BigDecimal rsi) {
        if (rsi == null) return false;
        return rsi.doubleValue() > 75.0;
    }
}