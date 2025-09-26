package com.quantum.backtest.infrastructure.adapter.out.strategy;

import com.quantum.backtest.domain.*;
import com.quantum.backtest.domain.strategy.StrategyCalculationLog;
import com.quantum.backtest.domain.strategy.StrategyContext;
import com.quantum.backtest.domain.strategy.TradingStrategy;
import com.quantum.backtest.domain.strategy.util.MovingAverageCalculator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 이동평균선 교차(Moving Average Crossover) 전략 구현
 * 단기 이동평균선(5일)이 장기 이동평균선(20일)을 돌파할 때 매매 신호 발생
 * - 골든크로스: 매수 신호 (단기선이 장기선을 상향 돌파)
 * - 데드크로스: 매도 신호 (단기선이 장기선을 하향 돌파)
 */
@Component
public class MovingAverageCrossoverStrategy implements TradingStrategy {

    private static final Logger log = LoggerFactory.getLogger(MovingAverageCrossoverStrategy.class);

    private static final int SHORT_MA_PERIOD = 5;  // 단기 이동평균 (5일)
    private static final int LONG_MA_PERIOD = 20;  // 장기 이동평균 (20일)

    @Override
    public StrategyType getStrategyType() {
        return StrategyType.MOVING_AVERAGE_CROSSOVER;
    }

    @Override
    public BacktestResult execute(StrategyContext context, List<PriceData> priceHistory) {
        log.info("이동평균선 교차 전략 실행 시작: {} - {} ({}일선/{})일선)",
                context.stockCode(), context.stockName(), SHORT_MA_PERIOD, LONG_MA_PERIOD);

        // 이동평균 계산 (로깅 포함)
        List<BigDecimal> shortMA = MovingAverageCalculator.calculateSMAWithLogging(context, priceHistory, SHORT_MA_PERIOD, "5일선");
        List<BigDecimal> longMA = MovingAverageCalculator.calculateSMAWithLogging(context, priceHistory, LONG_MA_PERIOD, "20일선");

        BigDecimal currentCapital = context.initialCapital();
        List<Trade> trades = new ArrayList<>();
        int currentPosition = 0; // 보유 주식 수
        int totalDays = priceHistory.size();
        int winTrades = 0;
        int lossTrades = 0;
        BigDecimal totalFees = BigDecimal.ZERO;

        // 백테스팅 실행 (장기 이동평균 기간 이후부터 시작)
        for (int i = LONG_MA_PERIOD; i < totalDays; i++) {
            PriceData currentDay = priceHistory.get(i);
            MovingAverageCalculator.CrossoverSignal signal =
                    MovingAverageCalculator.detectCrossoverWithLogging(context, shortMA, longMA, i, priceHistory);

            // 골든크로스: 매수 신호
            if (signal == MovingAverageCalculator.CrossoverSignal.GOLDEN_CROSS && currentPosition == 0) {
                BigDecimal buyPrice = currentDay.close();
                int quantity = currentCapital.divide(buyPrice, RoundingMode.DOWN).intValue();

                if (quantity > 0) {
                    Trade buyTrade = Trade.create(
                            currentDay.date().atTime(9, 0), // 장 시작 시간
                            TradeType.BUY,
                            buyPrice,
                            quantity,
                            String.format("골든크로스 매수 신호 (%d일선 > %d일선)", SHORT_MA_PERIOD, LONG_MA_PERIOD)
                    );

                    trades.add(buyTrade);
                    context.addTrade(buyTrade);

                    currentCapital = currentCapital.subtract(buyTrade.getActualAmount());
                    totalFees = totalFees.add(buyTrade.getActualAmount().subtract(buyTrade.amount()));
                    currentPosition = quantity;

                    // 매수 의사결정 로깅
                    logTradingDecision(context, currentDay, "BUY", buyPrice, quantity,
                            String.format("골든크로스 신호로 매수 결정: 5일선(%.2f) > 20일선(%.2f)",
                                    shortMA.get(i), longMA.get(i)), currentCapital);

                    log.debug("매수 실행: {} 주, 가격: {}, 잔여 자금: {}",
                            quantity, buyPrice, currentCapital);
                }
            }
            // 데드크로스: 매도 신호
            else if (signal == MovingAverageCalculator.CrossoverSignal.DEAD_CROSS && currentPosition > 0) {
                BigDecimal sellPrice = currentDay.close();

                Trade sellTrade = Trade.create(
                        currentDay.date().atTime(15, 0), // 장 마감 전
                        TradeType.SELL,
                        sellPrice,
                        currentPosition,
                        String.format("데드크로스 매도 신호 (%d일선 < %d일선)", SHORT_MA_PERIOD, LONG_MA_PERIOD)
                );

                trades.add(sellTrade);
                context.addTrade(sellTrade);

                BigDecimal sellAmount = sellTrade.getActualAmount();
                currentCapital = currentCapital.add(sellAmount);
                totalFees = totalFees.add(sellTrade.amount().subtract(sellAmount));

                // 수익/손실 판단
                Trade lastBuyTrade = findLastBuyTrade(trades);
                BigDecimal profit = BigDecimal.ZERO;
                if (lastBuyTrade != null) {
                    profit = sellAmount.subtract(lastBuyTrade.getActualAmount());
                    if (profit.compareTo(BigDecimal.ZERO) > 0) {
                        winTrades++;
                    } else {
                        lossTrades++;
                    }
                }

                // 매도 의사결정 로깅
                logTradingDecision(context, currentDay, "SELL", sellPrice, currentPosition,
                        String.format("데드크로스 신호로 매도 결정: 5일선(%.2f) < 20일선(%.2f), 수익: %s원",
                                shortMA.get(i), longMA.get(i), profit), currentCapital);

                log.debug("매도 실행: {} 주, 가격: {}, 총 자금: {}",
                        currentPosition, sellPrice, currentCapital);

                currentPosition = 0;
            }

            // 진행률 업데이트
            int progress = (i + 1) * 100 / totalDays;
            context.updateProgress(progress);
        }

        // 백테스팅 종료 시 보유 주식이 있다면 마지막 가격으로 매도
        if (currentPosition > 0) {
            PriceData lastDay = priceHistory.get(totalDays - 1);
            BigDecimal finalSellPrice = lastDay.close();

            Trade finalSellTrade = Trade.create(
                    lastDay.date().atTime(15, 30),
                    TradeType.SELL,
                    finalSellPrice,
                    currentPosition,
                    "백테스팅 종료 - 잔여 주식 매도"
            );

            trades.add(finalSellTrade);
            context.addTrade(finalSellTrade);

            BigDecimal finalSellAmount = finalSellTrade.getActualAmount();
            currentCapital = currentCapital.add(finalSellAmount);
            totalFees = totalFees.add(finalSellTrade.amount().subtract(finalSellAmount));

            // 마지막 거래 수익성 판단
            Trade lastBuyTrade = findLastBuyTrade(trades);
            if (lastBuyTrade != null) {
                BigDecimal profit = finalSellAmount.subtract(lastBuyTrade.getActualAmount());
                if (profit.compareTo(BigDecimal.ZERO) > 0) {
                    winTrades++;
                } else {
                    lossTrades++;
                }
            }
        }

        // 결과 계산
        int totalTrades = (winTrades + lossTrades);
        BacktestResult.Builder resultBuilder = new BacktestResult.Builder()
                .initialCapital(context.initialCapital())
                .finalCapital(currentCapital)
                .periodYears(context.getPeriodYears())
                .totalTrades(totalTrades)
                .winTrades(winTrades)
                .lossTrades(lossTrades)
                .totalFees(totalFees);

        BacktestResult result = resultBuilder.build();
        log.info("이동평균선 교차 전략 완료 - 초기자금: {}, 최종자금: {}, 수익률: {}%, " +
                 "총 거래: {}회 (승: {}회, 패: {}회, 승률: {}%)",
                context.initialCapital(), currentCapital, result.totalReturn(),
                totalTrades, winTrades, lossTrades, result.winRate());

        return result;
    }

    /**
     * 거래 의사결정 과정을 상세히 로깅
     */
    private void logTradingDecision(StrategyContext context, PriceData currentDay, String tradeType,
                                   BigDecimal price, int quantity, String reason, BigDecimal remainingCapital) {
        Map<String, Object> inputData = new HashMap<>();
        inputData.put("date", currentDay.date().toString());
        inputData.put("currentPrice", price.toString());
        inputData.put("tradeType", tradeType);
        inputData.put("quantity", quantity);

        Map<String, Object> decisionDetails = new HashMap<>();
        decisionDetails.put("reason", reason);
        decisionDetails.put("priceAnalysis", String.format("현재가: %s원, 거래수량: %d주", price, quantity));
        decisionDetails.put("capitalBefore", remainingCapital.toString());

        BigDecimal tradeAmount = price.multiply(BigDecimal.valueOf(quantity));
        if ("BUY".equals(tradeType)) {
            decisionDetails.put("capitalAfter", remainingCapital.subtract(tradeAmount).toString());
        } else {
            decisionDetails.put("capitalAfter", remainingCapital.add(tradeAmount).toString());
        }

        Map<String, Object> outputResult = new HashMap<>();
        outputResult.put("decision", tradeType);
        outputResult.put("tradeAmount", tradeAmount.toString());
        outputResult.put("executed", true);

        StrategyCalculationLog log = StrategyCalculationLog.forDecision(
                currentDay.date(),
                context.getStrategyType().name(),
                context.getNextStepSequence(),
                String.format("%s 결정: %s", tradeType.equals("BUY") ? "매수" : "매도", reason),
                inputData,
                decisionDetails,
                outputResult
        );

        context.addCalculationLog(log);
    }

    /**
     * 마지막 매수 거래를 찾아 반환
     */
    private Trade findLastBuyTrade(List<Trade> trades) {
        for (int i = trades.size() - 1; i >= 0; i--) {
            if (trades.get(i).type() == TradeType.BUY) {
                return trades.get(i);
            }
        }
        return null;
    }
}