package com.quantum.backtest.infrastructure.persistence;

import com.quantum.backtest.domain.*;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

/**
 * 백테스팅 JPA 엔티티
 */
@Entity
@Table(name = "backtests")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BacktestEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "backtest_uuid", nullable = false, unique = true, length = 36)
    private String backtestUuid;

    @Column(name = "stock_code", nullable = false, length = 10)
    private String stockCode;

    @Column(name = "stock_name", length = 100)
    private String stockName;

    @Enumerated(EnumType.STRING)
    @Column(name = "market_type", nullable = false)
    @Builder.Default
    private MarketType marketType = MarketType.DOMESTIC;

    @Column(name = "start_date", nullable = false)
    private LocalDate startDate;

    @Column(name = "end_date", nullable = false)
    private LocalDate endDate;

    @Column(name = "initial_capital", nullable = false, precision = 15, scale = 2)
    private BigDecimal initialCapital;

    @Enumerated(EnumType.STRING)
    @Column(name = "strategy_type", nullable = false)
    private StrategyType strategyType;

    @ElementCollection
    @CollectionTable(name = "backtest_strategy_params", joinColumns = @JoinColumn(name = "backtest_id"))
    @MapKeyColumn(name = "param_key")
    @Column(name = "param_value")
    @Builder.Default
    private Map<String, String> strategyParams = new HashMap<>();

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private BacktestStatus status;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "started_at")
    private LocalDateTime startedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Setter(AccessLevel.PUBLIC)
    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    @Column(name = "progress_percentage", nullable = false)
    @Builder.Default
    private Integer progressPercentage = 0;

    // 백테스팅 결과 필드들
    @Column(name = "total_return", precision = 8, scale = 4)
    private BigDecimal totalReturn;

    @Column(name = "annualized_return", precision = 8, scale = 4)
    private BigDecimal annualizedReturn;

    @Column(name = "max_drawdown", precision = 8, scale = 4)
    private BigDecimal maxDrawdown;

    @Column(name = "total_trades")
    private Integer totalTrades;

    @Column(name = "win_trades")
    private Integer winTrades;

    @Column(name = "loss_trades")
    private Integer lossTrades;

    @Column(name = "win_rate", precision = 8, scale = 4)
    private BigDecimal winRate;

    @Column(name = "sharpe_ratio", precision = 8, scale = 4)
    private BigDecimal sharpeRatio;

    @Column(name = "final_capital", precision = 15, scale = 2)
    private BigDecimal finalCapital;

    @Column(name = "total_fees", precision = 15, scale = 2)
    private BigDecimal totalFees;

    @OneToMany(mappedBy = "backtest", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @Builder.Default
    private List<TradeEntity> trades = new ArrayList<>();

    @OneToMany(cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @JoinColumn(name = "backtest_id", referencedColumnName = "backtest_uuid")
    @Builder.Default
    private List<StrategyExecutionLogEntity> strategyLogs = new ArrayList<>();

    /**
     * 도메인 객체로부터 엔티티를 생성한다.
     */
    public static BacktestEntity from(Backtest backtest) {
        BacktestEntity entity = new BacktestEntity();
        // Don't set Long ID - let Hibernate manage for new entities
        // Set UUID from domain object
        entity.backtestUuid = backtest.getId().value();
        entity.stockCode = backtest.getConfig().stockCode();
        entity.stockName = backtest.getConfig().stockName();
        entity.marketType = backtest.getConfig().marketType();
        entity.startDate = backtest.getConfig().startDate();
        entity.endDate = backtest.getConfig().endDate();
        entity.initialCapital = backtest.getConfig().initialCapital();
        entity.strategyType = backtest.getConfig().strategyType();
        entity.updateStrategyParams(backtest.getConfig().strategyParams());
        entity.status = backtest.getStatus();
        entity.createdAt = backtest.getCreatedAt();
        entity.startedAt = backtest.getStartedAt();
        entity.completedAt = backtest.getCompletedAt();
        entity.errorMessage = backtest.getErrorMessage();
        entity.progressPercentage = backtest.getProgressPercentage();

        BacktestResult result = backtest.getResult();
        if (result != null) {
            entity.totalReturn = result.totalReturn();
            entity.annualizedReturn = result.annualizedReturn();
            entity.maxDrawdown = result.maxDrawdown();
            entity.totalTrades = result.totalTrades();
            entity.winTrades = result.winTrades();
            entity.lossTrades = result.lossTrades();
            entity.winRate = result.winRate();
            entity.sharpeRatio = result.sharpeRatio();
            entity.finalCapital = result.finalCapital();
            entity.totalFees = result.totalFees();
        }

        // 거래 내역 매핑
        entity.trades = backtest.getTrades().stream()
                .map(trade -> TradeEntity.from(trade, entity))
                .toList();

        return entity;
    }

    /**
     * 엔티티를 도메인 객체로 변환한다.
     */
    public Backtest toDomain() {
        BacktestConfig config = new BacktestConfig(
                stockCode,
                stockName,
                marketType,
                startDate,
                endDate,
                initialCapital,
                strategyType,
                convertStrategyParams()
        );

        BacktestResult result = null;
        if (totalReturn != null) {
            result = new BacktestResult(
                    totalReturn,
                    annualizedReturn,
                    maxDrawdown,
                    totalTrades != null ? totalTrades : 0,
                    winTrades != null ? winTrades : 0,
                    lossTrades != null ? lossTrades : 0,
                    winRate,
                    sharpeRatio,
                    finalCapital,
                    totalFees
            );
        }

        List<Trade> domainTrades = trades.stream()
                .map(TradeEntity::toDomain)
                .toList();

        return new Backtest(
                BacktestId.from(backtestUuid),
                config,
                createdAt,
                status,
                startedAt,
                completedAt,
                result,
                errorMessage,
                domainTrades,
                progressPercentage != null ? progressPercentage : 0
        );
    }


    /**
     * 문자열 맵을 객체 맵으로 변환
     */
    private Map<String, Object> convertStrategyParams() {
        Map<String, Object> params = new HashMap<>();
        strategyParams.forEach((key, value) -> {
            if (value != null) {
                // 숫자 변환 시도
                try {
                    if (value.contains(".")) {
                        params.put(key, Double.parseDouble(value));
                    } else {
                        params.put(key, Integer.parseInt(value));
                    }
                } catch (NumberFormatException e) {
                    // 불린 변환 시도
                    if ("true".equalsIgnoreCase(value) || "false".equalsIgnoreCase(value)) {
                        params.put(key, Boolean.parseBoolean(value));
                    } else {
                        // 문자열로 유지
                        params.put(key, value);
                    }
                }
            }
        });
        return params;
    }

    /**
     * 전략 파라미터를 설정한다. (Lombok @Setter와 충돌 방지를 위한 커스텀 메소드)
     */
    public void updateStrategyParams(Map<String, Object> params) {
        this.strategyParams = new HashMap<>();
        if (params != null) {
            params.forEach((key, value) ->
                this.strategyParams.put(key, value != null ? value.toString() : null)
            );
        }
    }

}