package com.quantum.trading.platform.query.view;

import com.quantum.trading.platform.shared.value.Position;
import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.envers.Audited;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * 포지션 조회용 View (CQRS Read Model)
 * 
 * PortfolioView의 자식 엔티티
 */
@Entity
@Table(name = "position_view")
@Audited // Envers 감사 기능 활성화
@Data
@NoArgsConstructor
public class PositionView {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "symbol", nullable = false, length = 20)
    private String symbol;
    
    @Column(name = "symbol_name", length = 100)
    private String symbolName;
    
    @Column(name = "quantity", nullable = false)
    private Integer quantity;
    
    @Column(name = "average_price", nullable = false, precision = 19, scale = 2)
    private BigDecimal averagePrice;
    
    @Column(name = "current_price", precision = 19, scale = 2)
    private BigDecimal currentPrice;
    
    @Column(name = "market_value", precision = 19, scale = 2)
    private BigDecimal marketValue;
    
    @Column(name = "unrealized_pnl", precision = 19, scale = 2)
    private BigDecimal unrealizedPnl;
    
    @Column(name = "unrealized_pnl_percentage", precision = 5, scale = 2)
    private BigDecimal unrealizedPnlPercentage;
    
    @Column(name = "invested_amount", precision = 19, scale = 2)
    private BigDecimal investedAmount;
    
    @Column(name = "last_updated", nullable = false)
    private Instant lastUpdated;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "portfolio_id", nullable = false)
    private PortfolioView portfolioView;
    
    @Version
    private Long version;
    
    /**
     * 팩토리 메서드 - Position 도메인 객체로부터 생성
     */
    public static PositionView fromPosition(Position position, Instant timestamp) {
        PositionView view = new PositionView();
        view.symbol = position.getSymbol().value();
        view.quantity = position.getQuantity().value();
        view.averagePrice = position.getAveragePrice().amount();
        view.investedAmount = view.averagePrice.multiply(BigDecimal.valueOf(view.quantity));
        view.lastUpdated = timestamp;
        
        return view;
    }
    
    /**
     * 현재 시장 가격 업데이트
     */
    public void updateCurrentPrice(BigDecimal currentPrice, Instant timestamp) {
        this.currentPrice = currentPrice;
        this.lastUpdated = timestamp;
        recalculateMetrics();
    }
    
    /**
     * 수량 및 평균 단가 업데이트
     */
    public void updatePosition(Integer newQuantity, BigDecimal newAveragePrice, Instant timestamp) {
        this.quantity = newQuantity;
        this.averagePrice = newAveragePrice;
        this.investedAmount = newAveragePrice.multiply(BigDecimal.valueOf(newQuantity));
        this.lastUpdated = timestamp;
        recalculateMetrics();
    }
    
    /**
     * 메트릭 재계산
     */
    private void recalculateMetrics() {
        if (currentPrice != null) {
            this.marketValue = currentPrice.multiply(BigDecimal.valueOf(quantity));
            this.unrealizedPnl = marketValue.subtract(investedAmount);
            
            if (investedAmount.compareTo(BigDecimal.ZERO) > 0) {
                this.unrealizedPnlPercentage = unrealizedPnl
                        .divide(investedAmount, 4, BigDecimal.ROUND_HALF_UP)
                        .multiply(BigDecimal.valueOf(100));
            } else {
                this.unrealizedPnlPercentage = BigDecimal.ZERO;
            }
        } else {
            this.marketValue = BigDecimal.ZERO;
            this.unrealizedPnl = BigDecimal.ZERO;
            this.unrealizedPnlPercentage = BigDecimal.ZERO;
        }
    }
    
    /**
     * 수익률이 양수인지 확인
     */
    public boolean isProfitable() {
        return unrealizedPnl != null && unrealizedPnl.compareTo(BigDecimal.ZERO) > 0;
    }
    
    /**
     * 손실인지 확인
     */
    public boolean isLoss() {
        return unrealizedPnl != null && unrealizedPnl.compareTo(BigDecimal.ZERO) < 0;
    }
    
    /**
     * 포지션이 비어있는지 확인
     */
    public boolean isEmpty() {
        return quantity == null || quantity == 0;
    }
    
    /**
     * 현재 가격 대비 수익률 계산
     */
    public BigDecimal calculateReturnRate() {
        if (averagePrice.compareTo(BigDecimal.ZERO) == 0 || currentPrice == null) {
            return BigDecimal.ZERO;
        }
        
        return currentPrice.subtract(averagePrice)
                .divide(averagePrice, 4, BigDecimal.ROUND_HALF_UP)
                .multiply(BigDecimal.valueOf(100));
    }
}