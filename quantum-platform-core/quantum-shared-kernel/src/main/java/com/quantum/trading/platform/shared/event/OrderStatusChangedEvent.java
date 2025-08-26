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
}