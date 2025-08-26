package com.quantum.trading.platform.command.aggregate;

import com.quantum.trading.platform.shared.command.CancelOrderCommand;
import com.quantum.trading.platform.shared.command.CreateOrderCommand;
import com.quantum.trading.platform.shared.command.SubmitOrderToBrokerCommand;
import com.quantum.trading.platform.shared.event.*;
import com.quantum.trading.platform.shared.value.*;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateLifecycle;
import org.axonframework.spring.stereotype.Aggregate;

import java.time.Instant;

/**
 * 주문 Aggregate
 * 
 * Axon Framework Event Sourcing 기반의 주문 도메인 집합체
 * 모든 주문 관련 비즈니스 로직과 상태 관리를 담당
 */
@Aggregate
@NoArgsConstructor // Axon 요구사항
@Slf4j
public class TradingOrder {
    
    @AggregateIdentifier
    private OrderId orderId;
    private UserId userId;
    private Symbol symbol;
    private OrderType orderType;
    private OrderSide side;
    private Money price;
    private Quantity quantity;
    private OrderStatus status;
    private String brokerType;
    private String brokerOrderId;
    private Instant createdAt;
    private Instant updatedAt;
    
    /**
     * 새 주문 생성 - Aggregate 생성자
     */
    @CommandHandler
    public TradingOrder(CreateOrderCommand command) {
        log.info("Creating new order: {}", command.orderId());
        
        // 명령 검증
        command.validate();
        
        // 비즈니스 규칙 검증
        validateNewOrder(command);
        
        // 주문 생성 이벤트 발행
        AggregateLifecycle.apply(OrderCreatedEvent.create(
                command.orderId(),
                command.userId(),
                command.symbol(),
                command.orderType(),
                command.side(),
                command.price(),
                command.quantity()));
    }
    
    /**
     * 증권사에 주문 제출
     */
    @CommandHandler
    public void handle(SubmitOrderToBrokerCommand command) {
        log.info("Submitting order {} to broker {}", command.orderId(), command.brokerType());
        
        command.validate();
        
        // 현재 상태에서 제출 가능한지 검증
        if (this.status != OrderStatus.PENDING) {
            throw new IllegalStateException(
                String.format("Order %s cannot be submitted in status %s", 
                    this.orderId, this.status));
        }
        
        // 상태 변경 이벤트 발행
        AggregateLifecycle.apply(OrderStatusChangedEvent.create(
                this.orderId,
                this.status,
                OrderStatus.SUBMITTED,
                "Order submitted to broker " + command.brokerType()));
        
        // 증권사 제출 이벤트 발행
        AggregateLifecycle.apply(OrderSubmittedToBrokerEvent.create(
                this.orderId,
                command.brokerType(),
                null)); // 실제 제출 후 업데이트
    }
    
    /**
     * 주문 취소
     */
    @CommandHandler
    public void handle(CancelOrderCommand command) {
        log.info("Cancelling order {} with reason: {}", command.orderId(), command.reason());
        
        command.validate();
        
        // 취소 가능한 상태인지 검증
        if (!this.status.isCancellable()) {
            throw new IllegalStateException(
                String.format("Order %s cannot be cancelled in status %s", 
                    this.orderId, this.status));
        }
        
        // 주문 취소 이벤트 발행
        AggregateLifecycle.apply(OrderStatusChangedEvent.create(
                this.orderId,
                this.status,
                OrderStatus.CANCELLED,
                command.reason()));
    }
    
    /**
     * 주문 체결 처리
     */
    public void markAsExecuted(Money executedPrice, Quantity executedQuantity, 
                              Quantity remainingQuantity, String brokerOrderId, String executionId) {
        
        if (this.status != OrderStatus.SUBMITTED && this.status != OrderStatus.ACCEPTED 
            && this.status != OrderStatus.PARTIALLY_FILLED) {
            throw new IllegalStateException(
                String.format("Order %s cannot be executed in status %s", 
                    this.orderId, this.status));
        }
        
        // 체결 이벤트 발행
        AggregateLifecycle.apply(OrderExecutedEvent.create(
                this.orderId,
                executedPrice,
                executedQuantity,
                remainingQuantity,
                brokerOrderId,
                executionId));
        
        // 상태 변경 이벤트 발행
        OrderStatus newStatus = remainingQuantity.value() == 0 
            ? OrderStatus.FILLED 
            : OrderStatus.PARTIALLY_FILLED;
            
        AggregateLifecycle.apply(OrderStatusChangedEvent.create(
                this.orderId,
                this.status,
                newStatus,
                "Order executed: " + executedQuantity + " at " + executedPrice));
    }
    
    /**
     * Event Sourcing Handlers - 이벤트로부터 상태 복원
     */
    @EventSourcingHandler
    public void on(OrderCreatedEvent event) {
        this.orderId = event.orderId();
        this.userId = event.userId();
        this.symbol = event.symbol();
        this.orderType = event.orderType();
        this.side = event.side();
        this.price = event.price();
        this.quantity = event.quantity();
        this.status = OrderStatus.PENDING;
        this.createdAt = event.timestamp();
        this.updatedAt = event.timestamp();
        
        log.debug("Order created: {}", this.orderId);
    }
    
    @EventSourcingHandler
    public void on(OrderStatusChangedEvent event) {
        this.status = event.newStatus();
        this.updatedAt = event.timestamp();
        
        log.debug("Order {} status changed from {} to {}", 
            this.orderId, event.previousStatus(), event.newStatus());
    }
    
    @EventSourcingHandler
    public void on(OrderSubmittedToBrokerEvent event) {
        this.brokerType = event.brokerType();
        this.brokerOrderId = event.brokerOrderId();
        this.updatedAt = event.submittedAt();
        
        log.debug("Order {} submitted to broker {}", this.orderId, this.brokerType);
    }
    
    @EventSourcingHandler
    public void on(OrderExecutedEvent event) {
        this.updatedAt = event.getExecutedAt();
        
        log.debug("Order {} executed: {} at {}", 
            this.orderId, event.getExecutedQuantity(), event.getExecutedPrice());
    }
    
    /**
     * 비즈니스 규칙 검증
     */
    private void validateNewOrder(CreateOrderCommand command) {
        // 주문 수량 검증 (한국 주식은 1주 단위)
        if (command.quantity().value() <= 0) {
            throw new IllegalArgumentException("Order quantity must be positive");
        }
        
        // 가격 검증
        if (command.orderType().requiresPrice()) {
            if (command.price() == null || command.price().isZero()) {
                throw new IllegalArgumentException(
                    "Price is required for order type: " + command.orderType());
            }
            
            // 최소 가격 단위 검증 (한국 주식은 호가 단위 존재)
            validatePriceTickSize(command.price(), command.symbol());
        }
        
        // 시간외 거래 검증 (필요시 시장 시간 체크)
        if (command.orderType().isAfterHoursOrder()) {
            validateAfterHoursTrading(command);
        }
    }
    
    private void validatePriceTickSize(Money price, Symbol symbol) {
        // 한국 주식 호가 단위 검증
        // 실제 구현에서는 종목별 호가 단위를 확인해야 함
        // 여기서는 기본적인 검증만 수행
    }
    
    private void validateAfterHoursTrading(CreateOrderCommand command) {
        // 시간외 거래 조건 검증
        // 실제 구현에서는 시장 시간을 확인해야 함
    }
    
    // Getters for testing and debugging
    public OrderId getOrderId() { return orderId; }
    public OrderStatus getStatus() { return status; }
    public OrderType getOrderType() { return orderType; }
    public OrderSide getSide() { return side; }
    public Money getPrice() { return price; }
    public Quantity getQuantity() { return quantity; }
}