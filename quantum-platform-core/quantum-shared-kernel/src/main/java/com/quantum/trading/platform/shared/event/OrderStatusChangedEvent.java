package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.OrderId;
import com.quantum.trading.platform.shared.value.OrderStatus;

import java.time.Instant;

/**
 * 주문 상태 변경 이벤트
 * 
 * 주문의 상태가 변경되었을 때 발행되는 이벤트
 */
public record OrderStatusChangedEvent(
    OrderId orderId,
    OrderStatus previousStatus,
    OrderStatus newStatus,
    String reason,
    Instant timestamp
) {
    
    public static OrderStatusChangedEvent create(
            OrderId orderId,
            OrderStatus previousStatus,
            OrderStatus newStatus,
            String reason) {
        return new OrderStatusChangedEvent(
                orderId,
                previousStatus,
                newStatus,
                reason,
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
        private OrderStatus previousStatus;
        private OrderStatus newStatus;
        private String reason;
        private Instant timestamp;
        
        public Builder orderId(OrderId orderId) {
            this.orderId = orderId;
            return this;
        }
        
        public Builder previousStatus(OrderStatus previousStatus) {
            this.previousStatus = previousStatus;
            return this;
        }
        
        public Builder newStatus(OrderStatus newStatus) {
            this.newStatus = newStatus;
            return this;
        }
        
        public Builder reason(String reason) {
            this.reason = reason;
            return this;
        }
        
        public Builder timestamp(Instant timestamp) {
            this.timestamp = timestamp;
            return this;
        }
        
        public OrderStatusChangedEvent build() {
            if (timestamp == null) {
                timestamp = Instant.now();
            }
            return new OrderStatusChangedEvent(orderId, previousStatus, newStatus, reason, timestamp);
        }
    }
}