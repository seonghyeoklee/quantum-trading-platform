package com.quantum.trading.platform.query.view;

import com.quantum.trading.platform.shared.value.OrderSide;
import com.quantum.trading.platform.shared.value.OrderStatus;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.envers.Audited;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 거래 이력 View (TradeView)
 * 
 * 실제 체결된 거래 내역을 저장하는 독립적인 엔티티
 * OrderView와 별도로 관리되어 거래 이력 조회 성능을 최적화
 */
@Entity
@Table(name = "trade_view", indexes = {
    @Index(name = "idx_trade_user_id", columnList = "user_id"),
    @Index(name = "idx_trade_portfolio_id", columnList = "portfolio_id"), 
    @Index(name = "idx_trade_symbol", columnList = "symbol"),
    @Index(name = "idx_trade_executed_at", columnList = "executed_at"),
    @Index(name = "idx_trade_user_symbol_date", columnList = "user_id, symbol, executed_at")
})
@EntityListeners(AuditingEntityListener.class)
@Audited // Envers 감사 기능 활성화
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TradeView {
    
    @Id
    @Column(name = "trade_id", length = 50)
    private String tradeId;
    
    @Column(name = "order_id", nullable = false, length = 50)
    private String orderId;
    
    @Column(name = "user_id", nullable = false, length = 50)
    private String userId;
    
    @Column(name = "portfolio_id", nullable = false, length = 50)
    private String portfolioId;
    
    @Column(name = "symbol", nullable = false, length = 10)
    private String symbol;
    
    @Column(name = "symbol_name", length = 100)
    private String symbolName;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "side", nullable = false)
    private OrderSide side;
    
    @Column(name = "executed_quantity", nullable = false)
    private Integer executedQuantity;
    
    @Column(name = "executed_price", nullable = false, precision = 19, scale = 4)
    private BigDecimal executedPrice;
    
    @Column(name = "executed_amount", nullable = false, precision = 19, scale = 4)
    private BigDecimal executedAmount;
    
    @Column(name = "transaction_fee", precision = 19, scale = 4)
    private BigDecimal transactionFee;
    
    @Column(name = "securities_tax", precision = 19, scale = 4)
    private BigDecimal securitiesTax;
    
    @Column(name = "net_amount", nullable = false, precision = 19, scale = 4)
    private BigDecimal netAmount;
    
    @Column(name = "broker_order_id", length = 50)
    private String brokerOrderId;
    
    @Column(name = "broker_trade_id", length = 50)
    private String brokerTradeId;
    
    @Column(name = "executed_at", nullable = false)
    private LocalDateTime executedAt;
    
    @Column(name = "settlement_date")
    private LocalDateTime settlementDate;
    
    @Column(name = "currency", length = 10)
    @Builder.Default
    private String currency = "KRW";
    
    @Column(name = "market_type", length = 20)
    @Builder.Default
    private String marketType = "KOSPI";
    
    // P&L 관련 필드 (매도시)
    @Column(name = "average_cost", precision = 19, scale = 4)
    private BigDecimal averageCost;
    
    @Column(name = "realized_pnl", precision = 19, scale = 4)
    private BigDecimal realizedPnL;
    
    @Column(name = "realized_pnl_rate", precision = 10, scale = 6)
    private BigDecimal realizedPnLRate;
    
    // 메타데이터
    @Column(name = "order_status", nullable = false)
    @Enumerated(EnumType.STRING)
    @Builder.Default
    private OrderStatus orderStatus = OrderStatus.FILLED;
    
    @Column(name = "is_partial_fill")
    @Builder.Default
    private Boolean isPartialFill = false;
    
    @Column(name = "fill_sequence")
    @Builder.Default
    private Integer fillSequence = 1;
    
    @Column(name = "notes", length = 500)
    private String notes;
    
    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
    
    // 비즈니스 메서드
    
    /**
     * 매수 거래인지 확인
     */
    public boolean isBuyTrade() {
        return side == OrderSide.BUY;
    }
    
    /**
     * 매도 거래인지 확인
     */
    public boolean isSellTrade() {
        return side == OrderSide.SELL;
    }
    
    /**
     * 거래 총 비용 계산 (수수료 포함)
     */
    public BigDecimal getTotalCost() {
        return executedAmount.add(getTransactionFee()).add(getSecuritiesTax());
    }
    
    /**
     * 수수료 null 안전 반환
     */
    public BigDecimal getTransactionFee() {
        return transactionFee != null ? transactionFee : BigDecimal.ZERO;
    }
    
    /**
     * 증권거래세 null 안전 반환
     */
    public BigDecimal getSecuritiesTax() {
        return securitiesTax != null ? securitiesTax : BigDecimal.ZERO;
    }
    
    /**
     * 수익률 계산 (매도시)
     */
    public BigDecimal getPnLRate() {
        if (realizedPnLRate != null) {
            return realizedPnLRate;
        }
        
        if (isSellTrade() && averageCost != null && averageCost.compareTo(BigDecimal.ZERO) > 0) {
            return executedPrice.subtract(averageCost)
                    .divide(averageCost, 6, BigDecimal.ROUND_HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
        }
        
        return BigDecimal.ZERO;
    }
}