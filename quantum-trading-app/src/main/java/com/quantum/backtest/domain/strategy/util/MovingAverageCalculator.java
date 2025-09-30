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
 * 이동평균 계산 유틸리티
 * 기술적 분석에 사용되는 단순 이동평균(SMA) 계산
 */
public class MovingAverageCalculator {

    /**
     * 단순 이동평균(Simple Moving Average) 계산
     *
     * @param priceHistory 주가 데이터 리스트 (시간순 정렬)
     * @param period 이동평균 기간 (예: 5일, 20일)
     * @return 이동평균 값 리스트 (기간 미달 구간은 null)
     */
    public static List<BigDecimal> calculateSMA(List<PriceData> priceHistory, int period) {
        if (priceHistory == null || priceHistory.isEmpty() || period <= 0) {
            return new ArrayList<>();
        }

        List<BigDecimal> smaValues = new ArrayList<>();

        for (int i = 0; i < priceHistory.size(); i++) {
            if (i + 1 < period) {
                // 기간이 부족한 경우 null 추가
                smaValues.add(null);
            } else {
                // 이동평균 계산
                BigDecimal sum = BigDecimal.ZERO;
                for (int j = i - period + 1; j <= i; j++) {
                    sum = sum.add(priceHistory.get(j).close());
                }
                BigDecimal sma = sum.divide(BigDecimal.valueOf(period), 2, RoundingMode.HALF_UP);
                smaValues.add(sma);
            }
        }

        return smaValues;
    }

    /**
     * 특정 인덱스에서의 이동평균 값 계산
     *
     * @param priceHistory 주가 데이터 리스트
     * @param index 계산할 인덱스
     * @param period 이동평균 기간
     * @return 이동평균 값 (기간 부족시 null)
     */
    public static BigDecimal calculateSMAAt(List<PriceData> priceHistory, int index, int period) {
        if (priceHistory == null || index < 0 || index >= priceHistory.size() ||
            period <= 0 || index + 1 < period) {
            return null;
        }

        BigDecimal sum = BigDecimal.ZERO;
        for (int i = index - period + 1; i <= index; i++) {
            sum = sum.add(priceHistory.get(i).close());
        }

        return sum.divide(BigDecimal.valueOf(period), 2, RoundingMode.HALF_UP);
    }

    /**
     * 두 이동평균선의 교차 신호 감지
     *
     * @param shortMA 단기 이동평균 리스트
     * @param longMA 장기 이동평균 리스트
     * @param index 확인할 인덱스
     * @return 교차 신호 (GOLDEN_CROSS: 골든크로스, DEAD_CROSS: 데드크로스, NONE: 교차 없음)
     */
    public static CrossoverSignal detectCrossover(List<BigDecimal> shortMA, List<BigDecimal> longMA, int index) {
        if (shortMA == null || longMA == null ||
            index <= 0 || index >= shortMA.size() || index >= longMA.size()) {
            return CrossoverSignal.NONE;
        }

        BigDecimal currentShort = shortMA.get(index);
        BigDecimal currentLong = longMA.get(index);
        BigDecimal prevShort = shortMA.get(index - 1);
        BigDecimal prevLong = longMA.get(index - 1);

        // null 체크
        if (currentShort == null || currentLong == null || prevShort == null || prevLong == null) {
            return CrossoverSignal.NONE;
        }

        // 골든크로스: 단기선이 장기선을 아래에서 위로 돌파
        if (prevShort.compareTo(prevLong) <= 0 && currentShort.compareTo(currentLong) > 0) {
            return CrossoverSignal.GOLDEN_CROSS;
        }

        // 데드크로스: 단기선이 장기선을 위에서 아래로 돌파
        if (prevShort.compareTo(prevLong) >= 0 && currentShort.compareTo(currentLong) < 0) {
            return CrossoverSignal.DEAD_CROSS;
        }

        return CrossoverSignal.NONE;
    }

    /**
     * 교차 신호 타입
     */
    public enum CrossoverSignal {
        GOLDEN_CROSS,  // 골든크로스 (매수 신호)
        DEAD_CROSS,    // 데드크로스 (매도 신호)
        NONE           // 교차 없음
    }

    /**
     * 로깅 기능이 포함된 단순 이동평균(SMA) 계산 메서드
     * 계산 과정을 StrategyContext에 상세히 기록
     *
     * @param context       전략 실행 컨텍스트 (로깅용)
     * @param priceHistory  주가 데이터 리스트
     * @param period        이동평균 기간
     * @param maType        이동평균 타입 (5일, 20일 등)
     * @return 이동평균 값 리스트
     */
    public static List<BigDecimal> calculateSMAWithLogging(StrategyContext context,
                                                         List<PriceData> priceHistory,
                                                         int period,
                                                         String maType) {
        if (priceHistory == null || priceHistory.isEmpty() || period <= 0) {
            return new ArrayList<>();
        }

        List<BigDecimal> smaValues = new ArrayList<>();

        for (int i = 0; i < priceHistory.size(); i++) {
            if (i + 1 < period) {
                // 기간이 부족한 경우 null 추가
                smaValues.add(null);
            } else {
                // 현재 날짜의 데이터
                PriceData currentDay = priceHistory.get(i);

                // 이동평균 계산을 위한 가격 데이터 수집
                List<BigDecimal> pricesForCalculation = new ArrayList<>();
                BigDecimal sum = BigDecimal.ZERO;

                for (int j = i - period + 1; j <= i; j++) {
                    BigDecimal price = priceHistory.get(j).close();
                    pricesForCalculation.add(price);
                    sum = sum.add(price);
                }

                BigDecimal sma = sum.divide(BigDecimal.valueOf(period), 2, RoundingMode.HALF_UP);
                smaValues.add(sma);

                // 계산 과정 로깅 (매 10일마다 또는 중요한 시점)
                if (i % 10 == 0 || i == period - 1 || i == priceHistory.size() - 1) {
                    Map<String, Object> inputData = new HashMap<>();
                    inputData.put("period", period);
                    inputData.put("currentIndex", i);
                    inputData.put("priceRange", String.format("Day %d ~ %d", i - period + 1, i));

                    Map<String, Object> calculationDetails = new HashMap<>();
                    calculationDetails.put("prices", pricesForCalculation.stream()
                            .map(p -> p.toString()).toList());
                    calculationDetails.put("sum", sum.toString());
                    calculationDetails.put("divisor", period);
                    calculationDetails.put("calculation", String.format("(%s) / %d",
                            pricesForCalculation.stream()
                                    .map(BigDecimal::toString)
                                    .reduce((a, b) -> a + " + " + b)
                                    .orElse("0"), period));

                    Map<String, Object> outputResult = new HashMap<>();
                    outputResult.put("smaValue", sma.toString());
                    outputResult.put("maType", maType);

                    StrategyCalculationLog log = StrategyCalculationLog.forCalculation(
                            currentDay.date(),
                            context.getStrategyType().name(),
                            context.getNextStepSequence(),
                            String.format("%s일 이동평균 계산: %s", period, sma.toString()),
                            inputData,
                            calculationDetails,
                            outputResult
                    );

                    context.addCalculationLog(log);
                }
            }
        }

        return smaValues;
    }

    /**
     * 지수 이동평균(Exponential Moving Average) 계산
     *
     * @param priceHistory 주가 데이터 리스트 (시간순 정렬)
     * @param period 이동평균 기간
     * @return 지수 이동평균 값 리스트
     */
    public static List<BigDecimal> calculateEMA(List<PriceData> priceHistory, int period) {
        if (priceHistory == null || priceHistory.isEmpty() || period <= 0) {
            return new ArrayList<>();
        }

        List<BigDecimal> emaValues = new ArrayList<>();
        BigDecimal multiplier = BigDecimal.valueOf(2.0).divide(BigDecimal.valueOf(period + 1), 10, RoundingMode.HALF_UP);

        for (int i = 0; i < priceHistory.size(); i++) {
            if (i == 0) {
                // 첫 번째 EMA는 첫 번째 가격
                emaValues.add(priceHistory.get(i).close());
            } else {
                // EMA = (현재가격 * 승수) + (이전EMA * (1 - 승수))
                BigDecimal currentPrice = priceHistory.get(i).close();
                BigDecimal previousEMA = emaValues.get(i - 1);

                BigDecimal currentEMA = currentPrice.multiply(multiplier)
                        .add(previousEMA.multiply(BigDecimal.ONE.subtract(multiplier)));

                emaValues.add(currentEMA.setScale(2, RoundingMode.HALF_UP));
            }
        }

        return emaValues;
    }

    /**
     * 특정 인덱스에서의 EMA 값 계산
     *
     * @param priceHistory 주가 데이터 리스트
     * @param index 계산할 인덱스
     * @param period EMA 기간
     * @return EMA 값
     */
    public static BigDecimal calculateEMAAt(List<PriceData> priceHistory, int index, int period) {
        if (priceHistory == null || index < 0 || index >= priceHistory.size() || period <= 0) {
            return null;
        }

        List<BigDecimal> emaValues = calculateEMA(priceHistory.subList(0, index + 1), period);
        return emaValues.isEmpty() ? null : emaValues.get(emaValues.size() - 1);
    }

    /**
     * 로깅 기능이 포함된 교차 신호 감지 메서드
     * 교차 감지 과정을 StrategyContext에 상세히 기록
     */
    public static CrossoverSignal detectCrossoverWithLogging(StrategyContext context,
                                                           List<BigDecimal> shortMA,
                                                           List<BigDecimal> longMA,
                                                           int index,
                                                           List<PriceData> priceHistory) {
        if (shortMA == null || longMA == null ||
            index <= 0 || index >= shortMA.size() || index >= longMA.size()) {
            return CrossoverSignal.NONE;
        }

        BigDecimal currentShort = shortMA.get(index);
        BigDecimal currentLong = longMA.get(index);
        BigDecimal prevShort = shortMA.get(index - 1);
        BigDecimal prevLong = longMA.get(index - 1);

        // null 체크
        if (currentShort == null || currentLong == null || prevShort == null || prevLong == null) {
            return CrossoverSignal.NONE;
        }

        PriceData currentDay = priceHistory.get(index);
        CrossoverSignal signal = CrossoverSignal.NONE;

        // 골든크로스: 단기선이 장기선을 아래에서 위로 돌파
        if (prevShort.compareTo(prevLong) <= 0 && currentShort.compareTo(currentLong) > 0) {
            signal = CrossoverSignal.GOLDEN_CROSS;
        }
        // 데드크로스: 단기선이 장기선을 위에서 아래로 돌파
        else if (prevShort.compareTo(prevLong) >= 0 && currentShort.compareTo(currentLong) < 0) {
            signal = CrossoverSignal.DEAD_CROSS;
        }

        // 교차 신호가 발생한 경우에만 로깅
        if (signal != CrossoverSignal.NONE) {
            Map<String, Object> inputData = new HashMap<>();
            inputData.put("index", index);
            inputData.put("date", currentDay.date().toString());
            inputData.put("currentPrice", currentDay.close().toString());

            Map<String, Object> calculationDetails = new HashMap<>();
            calculationDetails.put("previousShortMA", prevShort.toString());
            calculationDetails.put("previousLongMA", prevLong.toString());
            calculationDetails.put("currentShortMA", currentShort.toString());
            calculationDetails.put("currentLongMA", currentLong.toString());
            calculationDetails.put("crossoverCondition",
                    signal == CrossoverSignal.GOLDEN_CROSS ?
                    "단기선이 장기선을 상향 돌파" : "단기선이 장기선을 하향 돌파");

            Map<String, Object> outputResult = new HashMap<>();
            outputResult.put("signal", signal.name());
            outputResult.put("signalType",
                    signal == CrossoverSignal.GOLDEN_CROSS ? "매수 신호" : "매도 신호");

            StrategyCalculationLog log = StrategyCalculationLog.forSignal(
                    currentDay.date(),
                    context.getStrategyType().name(),
                    context.getNextStepSequence(),
                    String.format("%s 감지 - 단기: %.2f, 장기: %.2f",
                            signal == CrossoverSignal.GOLDEN_CROSS ? "골든크로스" : "데드크로스",
                            currentShort, currentLong),
                    inputData,
                    calculationDetails,
                    outputResult
            );

            context.addCalculationLog(log);
        }

        return signal;
    }
}