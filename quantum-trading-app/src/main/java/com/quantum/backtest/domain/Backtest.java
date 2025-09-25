package com.quantum.backtest.domain;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * 백테스팅 Aggregate Root
 * 하나의 백테스팅 실행을 표현하는 도메인 엔티티
 */
public class Backtest {

    private final BacktestId id;
    private final BacktestConfig config;
    private final LocalDateTime createdAt;

    private BacktestStatus status;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private BacktestResult result;
    private String errorMessage;
    private final List<Trade> trades;
    private int progressPercentage;

    /**
     * 새로운 백테스팅을 생성한다.
     */
    public Backtest(BacktestConfig config) {
        this.id = BacktestId.generate();
        this.config = Objects.requireNonNull(config, "Config cannot be null");
        this.createdAt = LocalDateTime.now();
        this.status = BacktestStatus.PENDING;
        this.trades = new ArrayList<>();
        this.progressPercentage = 0;
    }

    /**
     * 기존 백테스팅을 복원한다. (JPA용)
     */
    public Backtest(BacktestId id, BacktestConfig config, LocalDateTime createdAt,
                    BacktestStatus status, LocalDateTime startedAt, LocalDateTime completedAt,
                    BacktestResult result, String errorMessage, List<Trade> trades, int progressPercentage) {
        this.id = Objects.requireNonNull(id, "Id cannot be null");
        this.config = Objects.requireNonNull(config, "Config cannot be null");
        this.createdAt = Objects.requireNonNull(createdAt, "Created at cannot be null");
        this.status = Objects.requireNonNull(status, "Status cannot be null");
        this.startedAt = startedAt;
        this.completedAt = completedAt;
        this.result = result;
        this.errorMessage = errorMessage;
        this.trades = trades != null ? new ArrayList<>(trades) : new ArrayList<>();
        this.progressPercentage = progressPercentage;
    }

    /**
     * 백테스팅 실행을 시작한다.
     */
    public void start() {
        if (!canStart()) {
            throw new IllegalStateException("Cannot start backtest in " + status + " status");
        }

        this.status = BacktestStatus.RUNNING;
        this.startedAt = LocalDateTime.now();
        this.progressPercentage = 0;
        this.trades.clear();
        this.result = null;
        this.errorMessage = null;
    }

    /**
     * 백테스팅 실행을 완료한다.
     */
    public void complete(BacktestResult result) {
        if (status != BacktestStatus.RUNNING) {
            throw new IllegalStateException("Cannot complete backtest in " + status + " status");
        }

        this.status = BacktestStatus.COMPLETED;
        this.completedAt = LocalDateTime.now();
        this.result = Objects.requireNonNull(result, "Result cannot be null");
        this.progressPercentage = 100;
    }

    /**
     * 백테스팅 실행을 실패로 처리한다.
     */
    public void fail(String errorMessage) {
        if (status != BacktestStatus.RUNNING) {
            throw new IllegalStateException("Cannot fail backtest in " + status + " status");
        }

        this.status = BacktestStatus.FAILED;
        this.completedAt = LocalDateTime.now();
        this.errorMessage = errorMessage;
    }

    /**
     * 백테스팅 실행을 취소한다.
     */
    public void cancel() {
        if (!canCancel()) {
            throw new IllegalStateException("Cannot cancel backtest in " + status + " status");
        }

        this.status = BacktestStatus.CANCELLED;
        this.completedAt = LocalDateTime.now();
    }

    /**
     * 거래를 추가한다.
     */
    public void addTrade(Trade trade) {
        if (status != BacktestStatus.RUNNING) {
            throw new IllegalStateException("Cannot add trade to backtest in " + status + " status");
        }

        this.trades.add(Objects.requireNonNull(trade, "Trade cannot be null"));
    }

    /**
     * 진행률을 업데이트한다.
     */
    public void updateProgress(int percentage) {
        if (status != BacktestStatus.RUNNING) {
            return;
        }

        if (percentage < 0 || percentage > 100) {
            throw new IllegalArgumentException("Progress percentage must be between 0 and 100");
        }

        this.progressPercentage = percentage;
    }

    // === 상태 확인 메서드들 ===

    /**
     * 백테스팅을 시작할 수 있는지 확인
     */
    public boolean canStart() {
        return status.canStart();
    }

    /**
     * 백테스팅을 취소할 수 있는지 확인
     */
    public boolean canCancel() {
        return status.canCancel();
    }

    /**
     * 백테스팅이 완료되었는지 확인
     */
    public boolean isFinished() {
        return status.isFinished();
    }

    /**
     * 백테스팅이 실행 중인지 확인
     */
    public boolean isRunning() {
        return status == BacktestStatus.RUNNING;
    }

    /**
     * 백테스팅이 성공했는지 확인
     */
    public boolean isCompleted() {
        return status == BacktestStatus.COMPLETED;
    }

    // === Getters ===

    public BacktestId getId() {
        return id;
    }

    public BacktestConfig getConfig() {
        return config;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public BacktestStatus getStatus() {
        return status;
    }

    public LocalDateTime getStartedAt() {
        return startedAt;
    }

    public LocalDateTime getCompletedAt() {
        return completedAt;
    }

    public BacktestResult getResult() {
        return result;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public List<Trade> getTrades() {
        return Collections.unmodifiableList(trades);
    }

    public int getProgressPercentage() {
        return progressPercentage;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Backtest backtest = (Backtest) o;
        return Objects.equals(id, backtest.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public String toString() {
        return "Backtest{" +
                "id=" + id +
                ", status=" + status +
                ", stockCode='" + config.stockCode() + '\'' +
                ", period=" + config.startDate() + "~" + config.endDate() +
                ", strategy=" + config.strategyType() +
                '}';
    }
}