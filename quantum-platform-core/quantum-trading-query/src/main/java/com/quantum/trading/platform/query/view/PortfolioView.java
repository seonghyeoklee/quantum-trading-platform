package com.quantum.trading.platform.query.view;

import com.quantum.trading.platform.shared.value.Money;
import com.quantum.trading.platform.shared.value.PortfolioId;
import com.quantum.trading.platform.shared.value.UserId;
import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/**
 * 포트폴리오 조회용 View (CQRS Read Model)
 *
 * 읽기 최적화된 비정규화 테이블
 */
@Entity
@Table(name = "portfolio_view")
@Data
@NoArgsConstructor
public class PortfolioView {

    @Id
    @Column(name = "portfolio_id")
    private String portfolioId;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(name = "cash_balance", nullable = false, precision = 19, scale = 2)
    private BigDecimal cashBalance;

    @Column(name = "total_invested", precision = 19, scale = 2)
    private BigDecimal totalInvested = BigDecimal.ZERO;

    @Column(name = "total_market_value", precision = 19, scale = 2)
    private BigDecimal totalMarketValue = BigDecimal.ZERO;

    @Column(name = "total_profit_loss", precision = 19, scale = 2)
    private BigDecimal totalProfitLoss = BigDecimal.ZERO;

    @Column(name = "profit_loss_percentage", precision = 5, scale = 2)
    private BigDecimal profitLossPercentage = BigDecimal.ZERO;

    @Column(name = "position_count")
    private Integer positionCount = 0;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @OneToMany(mappedBy = "portfolioView", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<PositionView> positions = new ArrayList<>();

    @Version
    private Long version;

    /**
     * 팩토리 메서드 - 포트폴리오 생성 이벤트로부터 생성
     */
    public static PortfolioView fromPortfolioCreated(
            PortfolioId portfolioId,
            UserId userId,
            Money initialCash,
            Instant timestamp) {

        PortfolioView view = new PortfolioView();
        view.portfolioId = portfolioId.id();
        view.userId = userId.value();
        view.cashBalance = initialCash.amount();
        view.createdAt = timestamp;
        view.updatedAt = timestamp;

        return view;
    }

    /**
     * 현금 잔액 업데이트
     */
    public void updateCashBalance(BigDecimal newBalance, Instant timestamp) {
        this.cashBalance = newBalance;
        this.updatedAt = timestamp;
    }

    /**
     * 이용 가능한 현금 (RiskManagementService용)
     */
    public Money getAvailableCash() {
        return Money.of(cashBalance);
    }

    /**
     * 총 포트폴리오 가치 (RiskManagementService용)
     */
    public Money getTotalValue() {
        return Money.of(cashBalance.add(totalMarketValue));
    }

    /**
     * 포지션 추가 또는 업데이트
     */
    public void updatePosition(PositionView positionView, Instant timestamp) {
        // 기존 포지션 제거
        positions.removeIf(p -> p.getSymbol().equals(positionView.getSymbol()));

        // 새 포지션이 비어있지 않으면 추가
        if (positionView.getQuantity() > 0) {
            positionView.setPortfolioView(this);
            positions.add(positionView);
        }

        recalculateMetrics();
        this.updatedAt = timestamp;
    }

    /**
     * 포트폴리오 메트릭 재계산
     */
    public void recalculateMetrics() {
        this.positionCount = positions.size();
        this.totalInvested = positions.stream()
                .map(p -> p.getAveragePrice().multiply(BigDecimal.valueOf(p.getQuantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        this.totalMarketValue = positions.stream()
                .map(PositionView::getMarketValue)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        this.totalProfitLoss = totalMarketValue.subtract(totalInvested);

        if (totalInvested.compareTo(BigDecimal.ZERO) > 0) {
            this.profitLossPercentage = totalProfitLoss
                    .divide(totalInvested, 4, BigDecimal.ROUND_HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
        } else {
            this.profitLossPercentage = BigDecimal.ZERO;
        }
    }

    /**
     * 총 포트폴리오 가치 (현금 + 주식 평가액)
     */
    public BigDecimal getTotalPortfolioValue() {
        return cashBalance.add(totalMarketValue);
    }

    /**
     * 특정 종목의 포지션 조회
     */
    public PositionView getPosition(String symbol) {
        return positions.stream()
                .filter(p -> p.getSymbol().equals(symbol))
                .findFirst()
                .orElse(null);
    }

    /**
     * 포지션 보유 여부 확인
     */
    public boolean hasPosition(String symbol) {
        return getPosition(symbol) != null;
    }

    /**
     * 포트폴리오가 비어있는지 확인
     */
    public boolean isEmpty() {
        return positions.isEmpty();
    }
}
