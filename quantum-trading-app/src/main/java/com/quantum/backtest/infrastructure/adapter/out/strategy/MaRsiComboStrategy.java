package com.quantum.backtest.infrastructure.adapter.out.strategy;

import com.quantum.backtest.domain.*;
import com.quantum.backtest.domain.strategy.StrategyCalculationLog;
import com.quantum.backtest.domain.strategy.StrategyContext;
import com.quantum.backtest.domain.strategy.TradingStrategy;
import com.quantum.backtest.domain.strategy.util.MovingAverageCalculator;
import com.quantum.backtest.domain.strategy.util.RSICalculator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 이동평균+RSI 조합 전략 구현
 * - 5일/20일 이동평균 교차와 RSI 신호를 결합한 하이브리드 전략
 * - 매수: Golden Cross + RSI 필터 (30 < RSI < 70)
 * - 매도: Dead Cross 또는 RSI 강한 과매수 (RSI > 75)
 */
@Component
public class MaRsiComboStrategy implements TradingStrategy {

    private static final Logger log = LoggerFactory.getLogger(MaRsiComboStrategy.class);

    private static final int SHORT_MA_PERIOD = 5;  // 단기 이동평균
    private static final int LONG_MA_PERIOD = 20;  // 장기 이동평균
    private static final int RSI_PERIOD = 14;      // RSI 계산 기간

    @Override
    public StrategyType getStrategyType() {
        return StrategyType.MA_RSI_COMBO;
    }

    @Override
    public BacktestResult execute(StrategyContext context, List<PriceData> priceHistory) {
        log.info("이동평균+RSI 조합 전략 실행 시작: {} - {}", context.stockCode(), context.stockName());

        if (priceHistory.size() < LONG_MA_PERIOD + RSI_PERIOD) {
            throw new IllegalArgumentException("가격 데이터가 부족합니다. 최소 " + (LONG_MA_PERIOD + RSI_PERIOD) + "일 필요");
        }

        BigDecimal currentCapital = context.initialCapital();
        int currentPosition = 0; // 보유 주식 수량
        BigDecimal averageBuyPrice = BigDecimal.ZERO; // 평균 매수가

        // 전략 시작 로깅
        context.addCalculationLog(StrategyCalculationLog.forCalculation(
                priceHistory.get(0).date(),
                getStrategyType().name(),
                context.getNextStepSequence(),
                String.format("MA+RSI 조합 전략 시작 - 초기자금: %s, 분석기간: %d일 (MA: %d/%d, RSI: %d)",
                        currentCapital, priceHistory.size(), SHORT_MA_PERIOD, LONG_MA_PERIOD, RSI_PERIOD),
                createCalculationData("초기자금", currentCapital, "총일수", priceHistory.size()),
                createCalculationData("단기MA", SHORT_MA_PERIOD, "장기MA", LONG_MA_PERIOD, "RSI기간", RSI_PERIOD),
                createCalculationData("전략", "MA_RSI_COMBO", "상태", "시작")
        ));

        // 이동평균 계산
        List<BigDecimal> shortMA = MovingAverageCalculator.calculateSMAWithLogging(
                context, priceHistory, SHORT_MA_PERIOD, "단기MA(" + SHORT_MA_PERIOD + "일)"
        );
        List<BigDecimal> longMA = MovingAverageCalculator.calculateSMAWithLogging(
                context, priceHistory, LONG_MA_PERIOD, "장기MA(" + LONG_MA_PERIOD + "일)"
        );

        // RSI 계산
        List<BigDecimal> rsiValues = RSICalculator.calculateRSIWithLogging(
                context, priceHistory, RSI_PERIOD, "RSI(" + RSI_PERIOD + "일)"
        );

        // 신호 분석 및 거래 실행
        int totalDays = priceHistory.size();
        int startIndex = Math.max(LONG_MA_PERIOD, RSI_PERIOD);

        for (int i = startIndex; i < totalDays; i++) {
            PriceData currentDay = priceHistory.get(i);
            PriceData previousDay = i > 0 ? priceHistory.get(i - 1) : null;

            BigDecimal currentPrice = currentDay.close();
            BigDecimal currentShortMA = shortMA.get(i);
            BigDecimal currentLongMA = longMA.get(i);
            BigDecimal currentRSI = rsiValues.get(i);

            // 이전일 데이터 (교차 확인용)
            BigDecimal prevShortMA = i > 0 ? shortMA.get(i - 1) : null;
            BigDecimal prevLongMA = i > 0 ? longMA.get(i - 1) : null;

            // 매수 신호 확인
            boolean goldenCross = isGoldenCross(prevShortMA, prevLongMA, currentShortMA, currentLongMA);
            boolean rsiFilter = currentRSI != null &&
                               currentRSI.doubleValue() > RSICalculator.OVERSOLD_THRESHOLD &&
                               currentRSI.doubleValue() < RSICalculator.OVERBOUGHT_THRESHOLD;

            boolean buySignal = goldenCross && rsiFilter && currentPosition == 0;

            // 매도 신호 확인
            boolean deadCross = isDeadCross(prevShortMA, prevLongMA, currentShortMA, currentLongMA);
            boolean strongOverbought = RSICalculator.isStrongSellCondition(currentRSI);
            boolean sellSignal = (deadCross || strongOverbought) && currentPosition > 0;

            // 매수 실행
            if (buySignal) {
                int quantity = currentCapital.divide(currentPrice, RoundingMode.DOWN).intValue();
                if (quantity > 0) {
                    Trade buyTrade = Trade.create(
                            currentDay.date().atTime(9, 30),
                            TradeType.BUY,
                            currentPrice,
                            quantity,
                            String.format("MA+RSI 조합 매수: Golden Cross + RSI %.2f", currentRSI.doubleValue())
                    );
                    context.addTrade(buyTrade);

                    currentCapital = currentCapital.subtract(buyTrade.getActualAmount());
                    currentPosition = quantity;
                    averageBuyPrice = currentPrice;

                    // 매수 로깅
                    context.addCalculationLog(StrategyCalculationLog.forTradeExecution(
                            currentDay.date(),
                            getStrategyType().name(),
                            context.getNextStepSequence(),
                            String.format("매수 실행: Golden Cross + RSI 필터 (%.2f) → %d주 × %s = %s",
                                    currentRSI.doubleValue(), quantity, currentPrice, buyTrade.getActualAmount()),
                            createCalculationData("신호", "BUY", "Golden Cross", goldenCross,
                                               "RSI", currentRSI.toString(), "RSI필터", rsiFilter),
                            createCalculationData("단기MA", currentShortMA.toString(), "장기MA", currentLongMA.toString(),
                                               "매수조건", "Golden Cross AND 30 < RSI < 70"),
                            createCalculationData("수량", quantity, "단가", currentPrice, "거래금액", buyTrade.getActualAmount(),
                                               "잔여자금", currentCapital)
                    ));
                }
            }

            // 매도 실행
            else if (sellSignal) {
                Trade sellTrade = Trade.create(
                        currentDay.date().atTime(15, 20),
                        TradeType.SELL,
                        currentPrice,
                        currentPosition,
                        String.format("MA+RSI 조합 매도: %s (RSI %.2f)",
                                deadCross ? "Dead Cross" : "RSI 강한 과매수",
                                currentRSI != null ? currentRSI.doubleValue() : 0.0)
                );
                context.addTrade(sellTrade);

                currentCapital = currentCapital.add(sellTrade.getActualAmount());

                // 수익률 계산
                BigDecimal profitLoss = currentPrice.subtract(averageBuyPrice).multiply(BigDecimal.valueOf(currentPosition));
                BigDecimal profitRate = currentPrice.subtract(averageBuyPrice)
                                               .divide(averageBuyPrice, 4, RoundingMode.HALF_UP)
                                               .multiply(BigDecimal.valueOf(100));

                // 매도 로깅
                context.addCalculationLog(StrategyCalculationLog.forTradeExecution(
                        currentDay.date(),
                        getStrategyType().name(),
                        context.getNextStepSequence(),
                        String.format("매도 실행: %s → %d주 × %s = %s (손익: %s, 수익률: %s%%)",
                                deadCross ? "Dead Cross" : "RSI 과매수",
                                currentPosition, currentPrice, sellTrade.getActualAmount(),
                                profitLoss.compareTo(BigDecimal.ZERO) > 0 ? "+" + profitLoss : profitLoss.toString(),
                                profitRate),
                        createCalculationData("신호", "SELL", "Dead Cross", deadCross,
                                           "RSI", currentRSI != null ? currentRSI.toString() : "N/A",
                                           "강한과매수", strongOverbought),
                        createCalculationData("단기MA", currentShortMA.toString(), "장기MA", currentLongMA.toString(),
                                           "매도조건", "Dead Cross OR RSI > 75"),
                        createCalculationData("수량", currentPosition, "단가", currentPrice,
                                           "거래금액", sellTrade.getActualAmount(), "손익", profitLoss,
                                           "수익률", profitRate + "%", "최종자금", currentCapital)
                ));

                currentPosition = 0;
                averageBuyPrice = BigDecimal.ZERO;
            }

            // 진행률 업데이트
            int progress = (i + 1) * 100 / totalDays;
            context.updateProgress(progress);
        }

        // 미결제 포지션 정리 (마지막날 강제 매도)
        if (currentPosition > 0) {
            PriceData lastDay = priceHistory.get(totalDays - 1);
            BigDecimal lastPrice = lastDay.close();

            Trade finalSellTrade = Trade.create(
                    lastDay.date().atTime(15, 30),
                    TradeType.SELL,
                    lastPrice,
                    currentPosition,
                    "기간 만료 - 포지션 정리"
            );
            context.addTrade(finalSellTrade);
            currentCapital = currentCapital.add(finalSellTrade.getActualAmount());

            // 최종 정리 로깅
            BigDecimal finalProfitLoss = lastPrice.subtract(averageBuyPrice).multiply(BigDecimal.valueOf(currentPosition));
            context.addCalculationLog(StrategyCalculationLog.forTradeExecution(
                    lastDay.date(),
                    getStrategyType().name(),
                    context.getNextStepSequence(),
                    String.format("기간 만료 매도: %d주 × %s = %s (최종 손익: %s)",
                            currentPosition, lastPrice, finalSellTrade.getActualAmount(), finalProfitLoss),
                    createCalculationData("사유", "기간만료", "수량", currentPosition, "단가", lastPrice),
                    createCalculationData("정리", "포지션정리", "매수가", averageBuyPrice),
                    createCalculationData("거래금액", finalSellTrade.getActualAmount(), "손익", finalProfitLoss,
                                       "최종자금", currentCapital)
            ));
        }

        // 백테스트 결과 계산
        List<Trade> trades = context.backtest().getTrades();
        BacktestResult.Builder resultBuilder = new BacktestResult.Builder()
                .initialCapital(context.initialCapital())
                .finalCapital(currentCapital)
                .periodYears(context.getPeriodYears())
                .totalTrades(trades.size() / 2); // 매수-매도 쌍의 개수

        // 거래 수수료 합계
        BigDecimal totalFees = trades.stream()
                .map(trade -> trade.amount().subtract(trade.getActualAmount()).abs())
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        resultBuilder.totalFees(totalFees);

        // 승률 계산
        int winTrades = 0;
        int lossTrades = 0;
        for (int i = 0; i < trades.size(); i += 2) {
            if (i + 1 < trades.size()) {
                Trade buyTrade = trades.get(i);
                Trade sellTrade = trades.get(i + 1);
                if (sellTrade.price().compareTo(buyTrade.price()) > 0) {
                    winTrades++;
                } else {
                    lossTrades++;
                }
            }
        }
        resultBuilder.winTrades(winTrades).lossTrades(lossTrades);

        BacktestResult result = resultBuilder.build();

        // 최종 결과 로깅
        context.addCalculationLog(StrategyCalculationLog.forCalculation(
                priceHistory.get(totalDays - 1).date(),
                getStrategyType().name(),
                context.getNextStepSequence(),
                String.format("MA+RSI 조합 전략 완료 - 초기: %s → 최종: %s (수익률: %s%%, 총거래: %d회, 승률: %s%%)",
                        context.initialCapital(), currentCapital, result.totalReturn(),
                        result.totalTrades(), result.winRate()),
                createCalculationData("초기자금", context.initialCapital(), "최종자금", currentCapital,
                                   "총거래수", result.totalTrades(), "총수수료", totalFees),
                createCalculationData("전략", "MA+RSI 조합", "수익률계산", "(최종-초기)/초기*100",
                                   "승률계산", "승리거래/총거래*100"),
                createCalculationData("수익률", result.totalReturn() + "%", "승률", result.winRate() + "%",
                                   "승리거래", winTrades, "손실거래", lossTrades,
                                   "수익성", result.isProfitable() ? "수익" : "손실")
        ));

        log.info("이동평균+RSI 조합 전략 완료 - 초기자금: {}, 최종자금: {}, 수익률: {}%, 총거래: {}회",
                context.initialCapital(), currentCapital, result.totalReturn(), result.totalTrades());

        return result;
    }

    /**
     * Golden Cross 확인 (단기MA가 장기MA를 상향 돌파)
     */
    private boolean isGoldenCross(BigDecimal prevShort, BigDecimal prevLong,
                                  BigDecimal currentShort, BigDecimal currentLong) {
        if (prevShort == null || prevLong == null || currentShort == null || currentLong == null) {
            return false;
        }

        return prevShort.compareTo(prevLong) <= 0 && currentShort.compareTo(currentLong) > 0;
    }

    /**
     * Dead Cross 확인 (단기MA가 장기MA를 하향 돌파)
     */
    private boolean isDeadCross(BigDecimal prevShort, BigDecimal prevLong,
                                BigDecimal currentShort, BigDecimal currentLong) {
        if (prevShort == null || prevLong == null || currentShort == null || currentLong == null) {
            return false;
        }

        return prevShort.compareTo(prevLong) >= 0 && currentShort.compareTo(currentLong) < 0;
    }

    /**
     * 계산 데이터 생성 헬퍼 메서드
     */
    private Map<String, Object> createCalculationData(Object... keyValuePairs) {
        Map<String, Object> data = new HashMap<>();
        for (int i = 0; i < keyValuePairs.length; i += 2) {
            if (i + 1 < keyValuePairs.length) {
                data.put(String.valueOf(keyValuePairs[i]), keyValuePairs[i + 1]);
            }
        }
        return data;
    }
}