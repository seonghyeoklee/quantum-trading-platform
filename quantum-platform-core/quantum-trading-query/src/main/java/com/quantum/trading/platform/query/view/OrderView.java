package com.quantum.trading.platform.query.view;

import com.quantum.trading.platform.shared.value.*;
import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.envers.Audited;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;

/**
 * 주문 조회용 View (CQRS Read Model)
 *
 * 읽기 최적화된 비정규화 테이블
 */
@Entity
@Table(name = "order_view")
@Audited // Envers 감사 기능 활성화
@Data
@NoArgsConstructor
public class OrderView {

    @Id
    @Column(name = "order_id")
    private String orderId;

    @Column(name = "user_id", nullable = false)
    private String userId;
    
    @Column(name = "portfolio_id", nullable = false)
    private String portfolioId;

    @Column(name = "symbol", nullable = false, length = 20)
    private String symbol;

    @Enumerated(EnumType.STRING)
    @Column(name = "order_type", nullable = false)
    private OrderType orderType;

    @Enumerated(EnumType.STRING)
    @Column(name = "side", nullable = false)
    private OrderSide side;

    @Column(name = "price", precision = 19, scale = 2)
    private BigDecimal price;
    
    @Column(name = "stop_price", precision = 19, scale = 2)
    private BigDecimal stopPrice;

    @Column(name = "quantity", nullable = false)
    private Integer quantity;
    
    @Column(name = "remaining_quantity")
    private Integer remainingQuantity;
    
    @Column(name = "average_price", precision = 19, scale = 2)
    private BigDecimal averagePrice;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private OrderStatus status;

    @Column(name = "broker_type", length = 20)
    private String brokerType;

    @Column(name = "account_number", length = 50)
    private String accountNumber;

    @Column(name = "broker_order_id", length = 100)
    private String brokerOrderId;

    @Column(name = "filled_quantity")
    private Integer filledQuantity;

    @Column(name = "filled_price", precision = 19, scale = 2)
    private BigDecimal filledPrice;

    @Column(name = "total_amount", precision = 19, scale = 2)
    private BigDecimal totalAmount;

    @Column(name = "fee", precision = 19, scale = 2)
    private BigDecimal fee;

    @Column(name = "cancellation_reason", length = 500)
    private String cancellationReason;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @Column(name = "submitted_at")
    private Instant submittedAt;

    @Column(name = "filled_at")
    private Instant filledAt;

    // Indexes for common queries
    @Version
    private Long version;

    /**
     * 팩토리 메서드 - 주문 생성 이벤트로부터 생성
     */
    public static OrderView fromOrderCreated(
            OrderId orderId,
            UserId userId,
            Symbol symbol,
            OrderType orderType,
            OrderSide side,
            Money price,
            Quantity quantity,
            Instant timestamp) {

        OrderView view = new OrderView();
        view.orderId = orderId.value();
        view.userId = userId.value();
        view.symbol = symbol.value();
        view.orderType = orderType;
        view.side = side;
        view.price = price != null ? price.amount() : null;
        view.quantity = quantity.value();
        view.status = OrderStatus.PENDING;
        view.filledQuantity = 0;
        view.createdAt = timestamp;
        view.updatedAt = timestamp;

        return view;
    }

    /**
     * 매수 주문인지 확인
     */
    public boolean isBuyOrder() {
        return side == OrderSide.BUY;
    }
    
    /**
     * LocalDateTime 어댑터 메서드들
     */
    public LocalDateTime getCreatedAt() {
        return createdAt != null ? LocalDateTime.ofInstant(createdAt, ZoneOffset.UTC) : null;
    }
    
    public LocalDateTime getUpdatedAt() {
        return updatedAt != null ? LocalDateTime.ofInstant(updatedAt, ZoneOffset.UTC) : null;
    }
    
    public LocalDateTime getSubmittedAt() {
        return submittedAt != null ? LocalDateTime.ofInstant(submittedAt, ZoneOffset.UTC) : null;
    }
    
    public LocalDateTime getFilledAt() {
        return filledAt != null ? LocalDateTime.ofInstant(filledAt, ZoneOffset.UTC) : null;
    }
    
    /**
     * 주문 상태 업데이트
     */
    public void updateStatus(OrderStatus newStatus, String reason, Instant timestamp) {
        this.status = newStatus;
        if (reason != null && newStatus == OrderStatus.CANCELLED) {
            this.cancellationReason = reason;
        }
        this.updatedAt = timestamp;

        if (newStatus == OrderStatus.SUBMITTED) {
            this.submittedAt = timestamp;
        } else if (newStatus == OrderStatus.FILLED) {
            this.filledAt = timestamp;
        }
    }

    /**
     * 브로커 제출 정보 업데이트
     */
    public void updateBrokerInfo(String brokerType, String accountNumber, Instant timestamp) {
        this.brokerType = brokerType;
        this.accountNumber = accountNumber;
        this.updatedAt = timestamp;
    }

    /**
     * 체결 정보 업데이트
     */
    public void updateExecution(
            Integer filledQuantity,
            BigDecimal filledPrice,
            BigDecimal totalAmount,
            BigDecimal fee,
            Instant timestamp) {

        this.filledQuantity = filledQuantity;
        this.filledPrice = filledPrice;
        this.totalAmount = totalAmount;
        this.fee = fee;
        this.updatedAt = timestamp;

        // 전량 체결되면 상태를 FILLED로 변경
        if (filledQuantity.equals(this.quantity)) {
            this.status = OrderStatus.FILLED;
            this.filledAt = timestamp;
        } else {
            this.status = OrderStatus.PARTIALLY_FILLED;
        }
    }

    /**
     * 주문이 완료 상태인지 확인
     */
    public boolean isCompleted() {
        return status == OrderStatus.FILLED ||
               status == OrderStatus.CANCELLED ||
               status == OrderStatus.REJECTED;
    }

    /**
     * 매도 주문인지 확인
     */
    public boolean isSellOrder() {
        return side == OrderSide.SELL;
    }

    /**
     * 지정가 주문인지 확인
     */
    public boolean isLimitOrder() {
        return orderType == OrderType.LIMIT;
    }

    /**
     * 시장가 주문인지 확인
     */
    public boolean isMarketOrder() {
        return orderType == OrderType.MARKET;
    }
}
