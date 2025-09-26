package com.quantum.backtest.infrastructure.adapter.out.strategy;

import com.quantum.backtest.domain.*;
import com.quantum.backtest.domain.strategy.StrategyCalculationLog;
import com.quantum.backtest.domain.strategy.StrategyContext;
import com.quantum.backtest.domain.strategy.TradingStrategy;
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
 * 매수후보유(Buy and Hold) 전략 구현
 * 첫 거래일에 전량 매수하여 마지막 거래일까지 보유하는 전략
 */
@Component
public class BuyAndHoldStrategy implements TradingStrategy {

    private static final Logger log = LoggerFactory.getLogger(BuyAndHoldStrategy.class);

    @Override
    public StrategyType getStrategyType() {
        return StrategyType.BUY_AND_HOLD;
    }

    @Override
    public BacktestResult execute(StrategyContext context, List<PriceData> priceHistory) {
        log.info("매수후보유 전략 실행 시작: {} - {}", context.stockCode(), context.stockName());

        BigDecimal currentCapital = context.initialCapital();
        int totalDays = priceHistory.size();

        // 전략 시작 로깅
        context.addCalculationLog(StrategyCalculationLog.forCalculation(
                priceHistory.get(0).date(),
                getStrategyType().name(),
                1,
                String.format("매수후보유 전략 시작 - 초기자금: %s, 분석기간: %d일",
                        currentCapital, totalDays),
                createCalculationData("초기자금", currentCapital, "분석기간", totalDays),
                new HashMap<>(),
                createCalculationData("전략", "BUY_AND_HOLD", "상태", "시작")
        ));

        // 첫 거래일에 전량 매수
        PriceData firstDay = priceHistory.get(0);
        BigDecimal buyPrice = firstDay.close();
        int quantity = currentCapital.divide(buyPrice, RoundingMode.DOWN).intValue();
        BigDecimal buyAmount = buyPrice.multiply(BigDecimal.valueOf(quantity));

        // 매수 계산 과정 로깅
        context.addCalculationLog(StrategyCalculationLog.forCalculation(
                firstDay.date(),
                getStrategyType().name(),
                2,
                String.format("매수 계산: 주가 %s → 구매가능 수량 %d주 (총 %s)",
                        buyPrice, quantity, buyAmount),
                createCalculationData("주가", buyPrice, "초기자금", currentCapital),
                createCalculationData("계산", "주식수량", "공식", "초기자금 ÷ 주가"),
                createCalculationData("수량", quantity, "매수금액", buyAmount)
        ));

        Trade buyTrade = Trade.create(
                firstDay.date().atStartOfDay(),
                TradeType.BUY,
                buyPrice,
                quantity,
                "매수후보유 전략 - 초기 매수"
        );
        context.addTrade(buyTrade);

        currentCapital = currentCapital.subtract(buyTrade.getActualAmount());

        // 매수 거래 실행 로깅
        context.addCalculationLog(StrategyCalculationLog.forTradeExecution(
                firstDay.date(),
                getStrategyType().name(),
                3,
                String.format("매수 거래 실행: %d주 × %s = %s (잔여자금: %s)",
                        quantity, buyPrice, buyTrade.getActualAmount(), currentCapital),
                createCalculationData("거래유형", "BUY", "수량", quantity, "단가", buyPrice),
                createCalculationData("실행", "매수거래", "수수료", "0.015%"),
                createCalculationData("거래금액", buyTrade.getActualAmount(), "잔여자금", currentCapital)
        ));

        // 진행률 업데이트
        for (int i = 0; i < totalDays; i++) {
            int progress = (i + 1) * 100 / totalDays;
            context.updateProgress(progress);
            log.debug("백테스팅 진행률: {}%", progress);
        }

        // 마지막 거래일에 전량 매도
        PriceData lastDay = priceHistory.get(totalDays - 1);
        BigDecimal sellPrice = lastDay.close();
        BigDecimal sellAmount = sellPrice.multiply(BigDecimal.valueOf(quantity));

        // 매도 계산 과정 로깅
        context.addCalculationLog(StrategyCalculationLog.forCalculation(
                lastDay.date(),
                getStrategyType().name(),
                4,
                String.format("매도 계산: %d주 × %s = %s (매수가 대비 %s%s)",
                        quantity, sellPrice, sellAmount,
                        sellPrice.compareTo(buyPrice) > 0 ? "+" : "",
                        sellPrice.subtract(buyPrice).multiply(BigDecimal.valueOf(quantity))),
                createCalculationData("매도주가", sellPrice, "수량", quantity, "매수가", buyPrice),
                createCalculationData("계산", "매도금액", "공식", "수량 × 매도주가"),
                createCalculationData("매도예상금액", sellAmount, "주당손익", sellPrice.subtract(buyPrice))
        ));

        Trade sellTrade = Trade.create(
                lastDay.date().atTime(15, 30), // 장 마감 시간
                TradeType.SELL,
                sellPrice,
                quantity,
                "매수후보유 전략 - 최종 매도"
        );
        context.addTrade(sellTrade);

        currentCapital = currentCapital.add(sellTrade.getActualAmount());

        // 매도 거래 실행 로깅
        context.addCalculationLog(StrategyCalculationLog.forTradeExecution(
                lastDay.date(),
                getStrategyType().name(),
                5,
                String.format("매도 거래 실행: %d주 × %s = %s (최종자금: %s)",
                        quantity, sellPrice, sellTrade.getActualAmount(), currentCapital),
                createCalculationData("거래유형", "SELL", "수량", quantity, "단가", sellPrice),
                createCalculationData("실행", "매도거래", "수수료", "0.015% + 세금 0.23%"),
                createCalculationData("거래금액", sellTrade.getActualAmount(), "최종자금", currentCapital)
        ));

        // 결과 계산
        BacktestResult.Builder resultBuilder = new BacktestResult.Builder()
                .initialCapital(context.initialCapital())
                .finalCapital(currentCapital)
                .periodYears(context.getPeriodYears())
                .totalTrades(1) // 1개 포지션 (매수→매도 세트)
                .totalFees(buyTrade.getActualAmount().subtract(buyTrade.amount())
                        .add(sellTrade.amount().subtract(sellTrade.getActualAmount())));

        // 수익성 판단
        if (currentCapital.compareTo(context.initialCapital()) > 0) {
            resultBuilder.winTrades(1).lossTrades(0);
        } else {
            resultBuilder.winTrades(0).lossTrades(1);
        }

        BacktestResult result = resultBuilder.build();

        // 최종 결과 로깅
        context.addCalculationLog(StrategyCalculationLog.forCalculation(
                lastDay.date(),
                getStrategyType().name(),
                6,
                String.format("전략 완료 - 초기자금: %s → 최종자금: %s (수익률: %s%%, 총 거래: %d회)",
                        context.initialCapital(), currentCapital, result.totalReturn(), result.totalTrades()),
                createCalculationData("초기자금", context.initialCapital(), "최종자금", currentCapital),
                createCalculationData("계산", "수익률", "공식", "(최종자금 - 초기자금) ÷ 초기자금 × 100"),
                createCalculationData("수익률", result.totalReturn(), "총거래", result.totalTrades(),
                        "수익성", result.isProfitable() ? "수익" : "손실")
        ));

        log.info("매수후보유 전략 완료 - 초기자금: {}, 최종자금: {}, 수익률: {}%",
                context.initialCapital(), currentCapital, result.totalReturn());

        return result;
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