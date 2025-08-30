package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.OrderId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

/**
 * 주문 취소 명령
 * 
 * 활성 상태의 주문을 취소하기 위한 명령
 */
public record CancelOrderCommand(
    @TargetAggregateIdentifier
    OrderId orderId,
    String reason
) {
    
    public void validate() {
        if (orderId == null) {
            throw new IllegalArgumentException("OrderId is required");
        }
        if (reason == null || reason.trim().isEmpty()) {
            throw new IllegalArgumentException("Cancellation reason is required");
        }
    }
    
    /**
     * Builder pattern support for test compatibility
     */
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private OrderId orderId;
        private String reason;
        
        public Builder orderId(OrderId orderId) {
            this.orderId = orderId;
            return this;
        }
        
        public Builder reason(String reason) {
            this.reason = reason;
            return this;
        }
        
        public CancelOrderCommand build() {
            return new CancelOrderCommand(orderId, reason);
        }
    }
}