package com.quantum.web.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.time.Duration;

/**
 * 자동매매 상태 엔티티
 *
 * 자동매매 실행 상태 및 성과를 추적하는 엔티티
 */
@Entity
@Table(name = "auto_trading_status")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AutoTradingStatus {

    @Id
    @Column(name = "id", length = 20)
    private String id;

    /**
     * 자동매매 설정 ID (외래키)
     */
    @Column(name = "config_id", nullable = false, length = 20)
    private String configId;

    /**
     * 자동매매 설정 엔티티 참조
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "config_id", insertable = false, updatable = false)
    private AutoTradingConfig config;

    /**
     * 현재 상태
     * - created: 초기 생성됨
     * - running: 실행 중
     * - paused: 일시 정지
     * - stopped: 정지됨
     * - error: 오류 발생
     */
    @Column(name = "status", nullable = false, length = 20)
    private String status;

    /**
     * 총 거래 횟수
     */
    @Column(name = "total_trades", nullable = false)
    @Builder.Default
    private Integer totalTrades = 0;

    /**
     * 수익 거래 횟수
     */
    @Column(name = "winning_trades", nullable = false)
    @Builder.Default
    private Integer winningTrades = 0;

    /**
     * 총 수익/손실 (절댓값)
     */
    @Column(name = "total_profit", nullable = false, precision = 15, scale = 2)
    @Builder.Default
    private BigDecimal totalProfit = BigDecimal.ZERO;

    /**
     * 총 수익률 (백분율)
     */
    @Column(name = "total_return", nullable = false, precision = 8, scale = 4)
    @Builder.Default
    private BigDecimal totalReturn = BigDecimal.ZERO;

    /**
     * 최대 낙폭 (백분율)
     */
    @Column(name = "max_drawdown", nullable = false, precision = 8, scale = 4)
    @Builder.Default
    private BigDecimal maxDrawdown = BigDecimal.ZERO;

    /**
     * 자동매매 시작 시각
     */
    @Column(name = "started_at")
    private LocalDateTime startedAt;

    /**
     * 자동매매 정지 시각
     */
    @Column(name = "stopped_at")
    private LocalDateTime stoppedAt;

    /**
     * 생성 일시
     */
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    /**
     * 수정 일시
     */
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    /**
     * 인덱스 설정
     */
    @Table(indexes = {
            @Index(name = "idx_config_id", columnList = "config_id"),
            @Index(name = "idx_status", columnList = "status"),
            @Index(name = "idx_updated_at", columnList = "updated_at")
    })

    /**
     * JPA 생명주기 콜백
     */
    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
        if (updatedAt == null) {
            updatedAt = LocalDateTime.now();
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    /**
     * 비즈니스 로직 메서드
     */

    /**
     * 승률 계산 (백분율)
     */
    public BigDecimal getWinRate() {
        if (totalTrades == null || totalTrades == 0) {
            return BigDecimal.ZERO;
        }

        return BigDecimal.valueOf(winningTrades)
                .divide(BigDecimal.valueOf(totalTrades), 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));
    }

    /**
     * 패배 거래 횟수 계산
     */
    public Integer getLosingTrades() {
        if (totalTrades == null || winningTrades == null) {
            return 0;
        }
        return totalTrades - winningTrades;
    }

    /**
     * 평균 거래당 수익률 계산
     */
    public BigDecimal getAverageReturn() {
        if (totalTrades == null || totalTrades == 0 || totalReturn == null) {
            return BigDecimal.ZERO;
        }

        return totalReturn.divide(BigDecimal.valueOf(totalTrades), 4, RoundingMode.HALF_UP);
    }

    /**
     * 실행 기간 계산 (분 단위)
     */
    public Long getRunningDurationMinutes() {
        if (startedAt == null) {
            return 0L;
        }

        LocalDateTime endTime = stoppedAt != null ? stoppedAt : LocalDateTime.now();
        return Duration.between(startedAt, endTime).toMinutes();
    }

    /**
     * 상태별 한글명 반환
     */
    public String getStatusKorean() {
        return switch (status) {
            case "created" -> "생성됨";
            case "running" -> "실행중";
            case "paused" -> "일시정지";
            case "stopped" -> "정지됨";
            case "error" -> "오류";
            default -> "알 수 없음";
        };
    }

    /**
     * 실행 가능 상태인지 확인
     */
    public boolean canStart() {
        return "created".equals(status) || "stopped".equals(status);
    }

    /**
     * 정지 가능 상태인지 확인
     */
    public boolean canStop() {
        return "running".equals(status) || "paused".equals(status);
    }

    /**
     * 일시정지 가능 상태인지 확인
     */
    public boolean canPause() {
        return "running".equals(status);
    }

    /**
     * 재개 가능 상태인지 확인
     */
    public boolean canResume() {
        return "paused".equals(status);
    }

    /**
     * 거래 결과 업데이트
     */
    public void updateTradeResult(BigDecimal tradeProfit, boolean isWinning) {
        if (tradeProfit == null) {
            return;
        }

        // 거래 횟수 증가
        this.totalTrades = (this.totalTrades == null ? 0 : this.totalTrades) + 1;

        // 수익 거래 횟수 업데이트
        if (isWinning) {
            this.winningTrades = (this.winningTrades == null ? 0 : this.winningTrades) + 1;
        }

        // 총 수익 업데이트
        this.totalProfit = (this.totalProfit == null ? BigDecimal.ZERO : this.totalProfit)
                .add(tradeProfit);

        // 총 수익률 재계산 (설정의 초기 자본 기준)
        if (config != null && config.getCapital() != null) {
            this.totalReturn = this.totalProfit
                    .divide(config.getCapital(), 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
        }

        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 최대 낙폭 업데이트
     */
    public void updateMaxDrawdown(BigDecimal currentDrawdown) {
        if (currentDrawdown == null) {
            return;
        }

        if (this.maxDrawdown == null || currentDrawdown.compareTo(this.maxDrawdown) > 0) {
            this.maxDrawdown = currentDrawdown;
            this.updatedAt = LocalDateTime.now();
        }
    }

    /**
     * 성과 요약 정보 생성
     */
    public String getPerformanceSummary() {
        return String.format("총 거래: %d회, 승률: %.1f%%, 총 수익률: %.2f%%, 최대 낙폭: %.2f%%",
                totalTrades,
                getWinRate(),
                totalReturn,
                maxDrawdown);
    }

    /**
     * 상태 리셋 (재시작 시 사용)
     */
    public void reset() {
        this.totalTrades = 0;
        this.winningTrades = 0;
        this.totalProfit = BigDecimal.ZERO;
        this.totalReturn = BigDecimal.ZERO;
        this.maxDrawdown = BigDecimal.ZERO;
        this.startedAt = null;
        this.stoppedAt = null;
        this.status = "created";
        this.updatedAt = LocalDateTime.now();
    }
}