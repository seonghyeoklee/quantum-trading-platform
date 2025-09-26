package com.quantum.backtest.application.service;

import com.quantum.backtest.application.port.in.CancelBacktestUseCase;
import com.quantum.backtest.application.port.in.GetBacktestUseCase;
import com.quantum.backtest.application.port.in.RunBacktestUseCase;
import com.quantum.backtest.application.port.out.BacktestRepositoryPort;
import com.quantum.backtest.application.port.out.MarketDataPort;
import com.quantum.backtest.domain.*;
import com.quantum.backtest.domain.strategy.StrategyCalculationLog;
import com.quantum.backtest.domain.strategy.StrategyContext;
import com.quantum.backtest.domain.strategy.TradingStrategy;
import com.quantum.backtest.infrastructure.adapter.out.strategy.StrategyFactory;
import com.quantum.backtest.infrastructure.persistence.JpaStrategyExecutionLogRepository;
import com.quantum.backtest.infrastructure.persistence.StrategyExecutionLogEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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
    private final StrategyFactory strategyFactory;
    private final JpaStrategyExecutionLogRepository strategyLogRepository;

    public BacktestApplicationService(BacktestRepositoryPort repositoryPort,
                                    MarketDataPort marketDataPort,
                                    StrategyFactory strategyFactory,
                                    JpaStrategyExecutionLogRepository strategyLogRepository) {
        this.repositoryPort = repositoryPort;
        this.marketDataPort = marketDataPort;
        this.strategyFactory = strategyFactory;
        this.strategyLogRepository = strategyLogRepository;
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
            BacktestResult result = executeStrategy(config, priceHistory, backtest);

            // 4. 백테스팅 완료 처리
            backtest.complete(result);

            // 5. 성공 시 즉시 저장
            try {
                repositoryPort.save(backtest);
                log.info("백테스팅 실행 및 저장 완료: {} - 총 수익률 {}%",
                        backtestId, result.totalReturn());
            } catch (Exception saveException) {
                log.error("백테스팅 완료 후 저장 실패: {} - 예외 타입: {}, 메시지: {}",
                         backtestId, saveException.getClass().getSimpleName(),
                         saveException.getMessage(), saveException);
            }

        } catch (Exception e) {
            log.error("백테스팅 실행 중 오류 발생: {} - {}", backtestId, e.getMessage(), e);

            // 예외 발생 시 실패 상태로 설정 및 저장
            if (backtest != null && backtest.isRunning()) {
                backtest.fail(e.getMessage());
                try {
                    repositoryPort.save(backtest);
                    log.debug("백테스팅 실패 상태 저장 완료: {} - {}", backtestId, backtest.getStatus());
                } catch (Exception saveException) {
                    log.error("백테스팅 실패 상태 저장 실패: {} - 예외 타입: {}, 메시지: {}",
                             backtestId, saveException.getClass().getSimpleName(),
                             saveException.getMessage(), saveException);
                }
            }
        }
    }

    /**
     * Strategy Pattern을 사용한 전략 실행
     */
    private BacktestResult executeStrategy(BacktestConfig config, List<PriceData> priceHistory, Backtest backtest) {
        log.info("전략 실행 시작: {} - {}", config.strategyType(), config.stockCode());

        // StrategyFactory에서 해당 전략 구현체를 가져와서 실행
        TradingStrategy strategy = strategyFactory.getStrategy(config.strategyType());
        StrategyContext context = StrategyContext.from(backtest);

        // 전략 실행
        BacktestResult result = strategy.execute(context, priceHistory);

        // 전략 실행 로그 저장
        saveStrategyExecutionLogs(backtest.getId(), context);

        return result;
    }

    /**
     * 전략 실행 로그 저장
     */
    private void saveStrategyExecutionLogs(BacktestId backtestId, StrategyContext context) {
        try {
            for (StrategyCalculationLog calculationLog : context.calculationLogs()) {
                StrategyExecutionLogEntity logEntity = StrategyExecutionLogEntity.from(calculationLog, backtestId.value());
                strategyLogRepository.save(logEntity);
            }

            log.info("전략 실행 로그 저장 완료: {} ({} 개)", backtestId, context.calculationLogs().size());
        } catch (Exception e) {
            log.error("전략 실행 로그 저장 실패: {} - {}", backtestId, e.getMessage(), e);
        }
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