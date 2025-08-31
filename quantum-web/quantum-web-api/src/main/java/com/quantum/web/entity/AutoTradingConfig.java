package com.quantum.web.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 자동매매 설정 엔티티
 *
 * 사용자가 설정한 자동매매 전략 및 파라미터를 저장하는 엔티티
 */
@Entity
@Table(name = "auto_trading_configs")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AutoTradingConfig {

    @Id
    @Column(name = "id", length = 20)
    private String id;

    /**
     * 자동매매 전략명
     * 예: "이동평균 교차 전략", "RSI 역추세 전략" 등
     */
    @Column(name = "strategy_name", nullable = false, length = 50)
    private String strategyName;

    /**
     * 거래 종목 코드
     * 예: "005930" (삼성전자)
     */
    @Column(name = "symbol", nullable = false, length = 6)
    private String symbol;

    /**
     * 투자 자본금
     */
    @Column(name = "capital", nullable = false, precision = 15, scale = 2)
    private BigDecimal capital;

    /**
     * 최대 포지션 크기 (백분율)
     * 예: 30 (전체 자본의 30%까지 투자)
     */
    @Column(name = "max_position_size", nullable = false)
    private Integer maxPositionSize;

    /**
     * 손절 비율 (백분율)
     * 예: 5.0 (5% 손실 시 손절)
     */
    @Column(name = "stop_loss_percent", nullable = false, precision = 5, scale = 2)
    private BigDecimal stopLossPercent;

    /**
     * 익절 비율 (백분율)
     * 예: 10.0 (10% 수익 시 익절)
     */
    @Column(name = "take_profit_percent", nullable = false, precision = 5, scale = 2)
    private BigDecimal takeProfitPercent;

    /**
     * 활성화 여부
     * true: 자동매매 활성, false: 비활성
     */
    @Column(name = "is_active", nullable = false)
    private Boolean isActive;

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
     * 복합 인덱스 설정
     * 활성화된 설정에서 전략명+종목으로 유니크 제약
     */
    @Table(indexes = {
            @Index(name = "idx_strategy_symbol_active", columnList = "strategy_name, symbol, is_active"),
            @Index(name = "idx_symbol_active", columnList = "symbol, is_active"),
            @Index(name = "idx_created_at", columnList = "created_at")
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
     * 설정이 유효한지 검증
     */
    public boolean isValid() {
        return strategyName != null && !strategyName.trim().isEmpty()
                && symbol != null && symbol.matches("^[A-Z0-9]{6}$")
                && capital != null && capital.compareTo(BigDecimal.ZERO) > 0
                && maxPositionSize != null && maxPositionSize > 0 && maxPositionSize <= 100
                && stopLossPercent != null && stopLossPercent.compareTo(BigDecimal.ZERO) > 0
                && takeProfitPercent != null && takeProfitPercent.compareTo(BigDecimal.ZERO) > 0
                && takeProfitPercent.compareTo(stopLossPercent) > 0;
    }

    /**
     * 최대 투자 금액 계산
     */
    public BigDecimal getMaxInvestmentAmount() {
        if (capital == null || maxPositionSize == null) {
            return BigDecimal.ZERO;
        }
        
        return capital.multiply(BigDecimal.valueOf(maxPositionSize))
                     .divide(BigDecimal.valueOf(100), 2, BigDecimal.ROUND_HALF_UP);
    }

    /**
     * 손절가 계산
     */
    public BigDecimal calculateStopLossPrice(BigDecimal entryPrice) {
        if (entryPrice == null || stopLossPercent == null) {
            return BigDecimal.ZERO;
        }
        
        BigDecimal stopLossAmount = entryPrice.multiply(stopLossPercent)
                                            .divide(BigDecimal.valueOf(100), 2, BigDecimal.ROUND_HALF_UP);
        
        return entryPrice.subtract(stopLossAmount);
    }

    /**
     * 익절가 계산
     */
    public BigDecimal calculateTakeProfitPrice(BigDecimal entryPrice) {
        if (entryPrice == null || takeProfitPercent == null) {
            return BigDecimal.ZERO;
        }
        
        BigDecimal takeProfitAmount = entryPrice.multiply(takeProfitPercent)
                                               .divide(BigDecimal.valueOf(100), 2, BigDecimal.ROUND_HALF_UP);
        
        return entryPrice.add(takeProfitAmount);
    }

    /**
     * 설정 요약 정보 생성
     */
    public String getSummary() {
        return String.format("[%s] %s - 자본: %s원, 포지션: %d%%, 손절: %.2f%%, 익절: %.2f%%",
                symbol, strategyName, capital.toPlainString(), maxPositionSize, 
                stopLossPercent, takeProfitPercent);
    }
}