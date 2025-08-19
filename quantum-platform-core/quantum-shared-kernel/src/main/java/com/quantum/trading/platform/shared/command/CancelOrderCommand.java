package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.OrderId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

/**
 * 주문 취소 명령
 * 
 * 활성 상태의 주문을 취소하기 위한 명령
 */
@Value
@Builder
public class CancelOrderCommand {
    @TargetAggregateIdentifier
    OrderId orderId;
    String reason;
    
    public void validate() {
        if (orderId == null) {
            throw new IllegalArgumentException("OrderId is required");
        }
        if (reason == null || reason.trim().isEmpty()) {
            throw new IllegalArgumentException("Cancellation reason is required");
        }
    }
}