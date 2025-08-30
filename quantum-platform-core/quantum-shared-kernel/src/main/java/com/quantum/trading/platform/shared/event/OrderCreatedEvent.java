package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.*;

import java.time.Instant;

/**
 * 주문 생성 이벤트
 * 
 * 새로운 주문이 생성되었을 때 발행되는 도메인 이벤트
 * Axon Framework에서 Event Sourcing의 핵심 이벤트
 */
public record OrderCreatedEvent(
    OrderId orderId,
    UserId userId,
    Symbol symbol,
    OrderType orderType,
    OrderSide side,
    Money price,
    Quantity quantity,
    Instant timestamp
) {
    
    public static OrderCreatedEvent create(
            OrderId orderId,
            UserId userId,
            Symbol symbol,
            OrderType orderType,
            OrderSide side,
            Money price,
            Quantity quantity) {
        return new OrderCreatedEvent(
                orderId,
                userId,
                symbol,
                orderType,
                side,
                price,
                quantity,
                Instant.now());
    }
    
    /**
     * Builder pattern support for test compatibility
     */
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private OrderId orderId;
        private UserId userId;
        private Symbol symbol;
        private OrderType orderType;
        private OrderSide side;
        private Money price;
        private Quantity quantity;
        private Instant timestamp;
        
        public Builder orderId(OrderId orderId) {
            this.orderId = orderId;
            return this;
        }
        
        public Builder userId(UserId userId) {
            this.userId = userId;
            return this;
        }
        
        public Builder symbol(Symbol symbol) {
            this.symbol = symbol;
            return this;
        }
        
        public Builder orderType(OrderType orderType) {
            this.orderType = orderType;
            return this;
        }
        
        public Builder side(OrderSide side) {
            this.side = side;
            return this;
        }
        
        public Builder price(Money price) {
            this.price = price;
            return this;
        }
        
        public Builder quantity(Quantity quantity) {
            this.quantity = quantity;
            return this;
        }
        
        public Builder timestamp(Instant timestamp) {
            this.timestamp = timestamp;
            return this;
        }
        
        public OrderCreatedEvent build() {
            if (timestamp == null) {
                timestamp = Instant.now();
            }
            return new OrderCreatedEvent(orderId, userId, symbol, orderType, side, price, quantity, timestamp);
        }
    }
}