package com.quantum.backtest.application.service;

import com.quantum.backtest.application.port.in.CancelBacktestUseCase;
import com.quantum.backtest.application.port.in.GetBacktestUseCase;
import com.quantum.backtest.application.port.in.RunBacktestUseCase;
import com.quantum.backtest.application.port.out.BacktestRepositoryPort;
import com.quantum.backtest.application.port.out.MarketDataPort;
import com.quantum.backtest.domain.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 백테스팅 Application Service
 * 모든 백테스팅 관련 Use Case를 구현
 */
@Service
@Transactional
public class BacktestApplicationService implements
        RunBacktestUseCase, GetBacktestUseCase, CancelBacktestUseCase {

    private static final Logger log = LoggerFactory.getLogger(BacktestApplicationService.class);

    private final BacktestRepositoryPort repositoryPort;
    private final MarketDataPort marketDataPort;
    public BacktestApplicationService(BacktestRepositoryPort repositoryPort,
                                    MarketDataPort marketDataPort) {
        this.repositoryPort = repositoryPort;
        this.marketDataPort = marketDataPort;
    }

    @Override
    public BacktestId runBacktest(BacktestConfig config) {
        log.info("=== 백테스팅 실행 시작: {} ({} ~ {}) ===",
                config.stockCode(), config.startDate(), config.endDate());

        try {
            // 1. 종목 유효성 검증
            if (!marketDataPort.isValidStock(config.stockCode())) {
                throw new IllegalArgumentException("유효하지 않은 종목코드: " + config.stockCode());
            }

            // 2. 백테스팅 생성 및 저장
            Backtest backtest = new Backtest(config);
            Backtest savedBacktest = repositoryPort.save(backtest);

            // 3. 동기적으로 백테스팅 실행 (ID로 조회하여 실행)
            executeBacktest(savedBacktest.getId());

            log.info("백테스팅 실행 요청 완료: ID {}", savedBacktest.getId());
            return savedBacktest.getId();

        } catch (Exception e) {
            log.error("백테스팅 실행 실패: {}", e.getMessage(), e);
            throw new RuntimeException("백테스팅 실행 중 오류가 발생했습니다: " + e.getMessage(), e);
        }
    }


    /**
     * 백테스팅을 실제로 실행한다. (동기적 실행)
     */
    @Transactional
    public void executeBacktest(BacktestId backtestId) {
        log.info("백테스팅 실행 시작: {}", backtestId);

        Backtest backtest = null;
        try {
            // 1. 백테스팅 조회 및 시작 처리
            backtest = repositoryPort.findById(backtestId)
                    .orElseThrow(() -> new IllegalArgumentException("백테스팅을 찾을 수 없습니다: " + backtestId));

            backtest.start();

            // 2. 주가 데이터 조회
            BacktestConfig config = backtest.getConfig();
            List<PriceData> priceHistory = marketDataPort.getPriceHistory(
                    config.stockCode(), config.startDate(), config.endDate());

            if (priceHistory.isEmpty()) {
                backtest.fail("주가 데이터를 조회할 수 없습니다.");
                repositoryPort.save(backtest); // 실패 시에는 즉시 저장 (메소드 종료)
                return;
            }

            log.info("주가 데이터 조회 완료: {} 건", priceHistory.size());

            // 3. 전략에 따른 백테스팅 실행
            BacktestResult result = runStrategy(config, priceHistory, backtest);

            // 4. 백테스팅 완료 처리
            backtest.complete(result);

            log.info("백테스팅 실행 완료: {} - 총 수익률 {}%",
                    backtestId, result.totalReturn());

        } catch (Exception e) {
            log.error("백테스팅 실행 중 오류 발생: {} - {}", backtestId, e.getMessage(), e);

            // 예외 발생 시 실패 상태로 설정
            if (backtest != null && backtest.isRunning()) {
                backtest.fail(e.getMessage());
            }
        } finally {
            // 성공/실패에 상관없이 최종 상태를 저장
            if (backtest != null) {
                try {
                    repositoryPort.save(backtest);
                    log.debug("백테스팅 최종 상태 저장 완료: {} - {}", backtestId, backtest.getStatus());
                } catch (Exception saveException) {
                    log.error("백테스팅 최종 상태 저장 실패: {} - {}", backtestId, saveException.getMessage());
                }
            }
        }
    }

    /**
     * 전략에 따른 백테스팅을 실행한다.
     */
    private BacktestResult runStrategy(BacktestConfig config, List<PriceData> priceHistory, Backtest backtest) {
        log.info("전략 실행 시작: {} - {}", config.strategyType(), config.stockCode());

        // 현재는 매수후보유 전략만 구현
        if (config.strategyType() == StrategyType.BUY_AND_HOLD) {
            return runBuyAndHoldStrategy(config, priceHistory, backtest);
        } else {
            throw new UnsupportedOperationException("아직 지원하지 않는 전략입니다: " + config.strategyType());
        }
    }

    /**
     * 매수후보유 전략 실행
     */
    private BacktestResult runBuyAndHoldStrategy(BacktestConfig config, List<PriceData> priceHistory, Backtest backtest) {
        BigDecimal currentCapital = config.initialCapital();
        List<Trade> trades = new ArrayList<>();
        int totalDays = priceHistory.size();

        // 첫 거래일에 전량 매수
        PriceData firstDay = priceHistory.get(0);
        BigDecimal buyPrice = firstDay.close();
        int quantity = currentCapital.divide(buyPrice, RoundingMode.DOWN).intValue();
        BigDecimal buyAmount = buyPrice.multiply(BigDecimal.valueOf(quantity));

        Trade buyTrade = Trade.create(
                firstDay.date().atStartOfDay(),
                TradeType.BUY,
                buyPrice,
                quantity,
                "매수후보유 전략 - 초기 매수"
        );
        trades.add(buyTrade);
        backtest.addTrade(buyTrade);

        currentCapital = currentCapital.subtract(buyTrade.getActualAmount());

        // 진행률 업데이트 (저장은 최소화)
        for (int i = 0; i < totalDays; i++) {
            int progress = (i + 1) * 100 / totalDays;
            backtest.updateProgress(progress);

            // Progress updates only stored in memory during execution
            // Final progress will be saved at completion
            log.debug("백테스팅 진행률: {}%", progress);
        }

        // 마지막 거래일에 전량 매도
        PriceData lastDay = priceHistory.get(totalDays - 1);
        BigDecimal sellPrice = lastDay.close();
        BigDecimal sellAmount = sellPrice.multiply(BigDecimal.valueOf(quantity));

        Trade sellTrade = Trade.create(
                lastDay.date().atTime(15, 30), // 장 마감 시간
                TradeType.SELL,
                sellPrice,
                quantity,
                "매수후보유 전략 - 최종 매도"
        );
        trades.add(sellTrade);
        backtest.addTrade(sellTrade);

        currentCapital = currentCapital.add(sellTrade.getActualAmount());

        // 결과 계산
        BacktestResult.Builder resultBuilder = new BacktestResult.Builder()
                .initialCapital(config.initialCapital())
                .finalCapital(currentCapital)
                .periodYears(config.getPeriodYears())
                .totalTrades(2) // 매수 1회, 매도 1회
                .totalFees(buyTrade.getActualAmount().subtract(buyTrade.amount())
                        .add(sellTrade.amount().subtract(sellTrade.getActualAmount())));

        // 수익성 판단
        if (currentCapital.compareTo(config.initialCapital()) > 0) {
            resultBuilder.winTrades(1).lossTrades(0);
        } else {
            resultBuilder.winTrades(0).lossTrades(1);
        }

        BacktestResult result = resultBuilder.build();
        log.info("매수후보유 전략 완료 - 초기자금: {}, 최종자금: {}, 수익률: {}%",
                config.initialCapital(), currentCapital, result.totalReturn());

        return result;
    }

    @Override
    public Optional<Backtest> getBacktest(BacktestId id) {
        return repositoryPort.findById(id);
    }

    @Override
    public Page<Backtest> getAllBacktests(Pageable pageable) {
        return repositoryPort.findAll(pageable);
    }

    @Override
    public Optional<Backtest> getBacktestDetail(BacktestId id) {
        // 거래 내역까지 포함한 상세 조회
        return repositoryPort.findById(id);
    }

    @Override
    public void cancelBacktest(BacktestId id) {
        log.info("백테스팅 취소 요청: {}", id);

        Backtest backtest = repositoryPort.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("백테스팅을 찾을 수 없습니다: " + id));

        if (!backtest.canCancel()) {
            throw new IllegalStateException("현재 상태에서는 백테스팅을 취소할 수 없습니다: " + backtest.getStatus());
        }

        backtest.cancel();
        repositoryPort.save(backtest);

        log.info("백테스팅 취소 완료: {}", id);
    }
}