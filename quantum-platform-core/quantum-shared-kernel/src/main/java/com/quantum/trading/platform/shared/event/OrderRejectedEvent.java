package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.OrderId;
import com.quantum.trading.platform.shared.value.OrderStatus;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 주문 거부 이벤트
 */
@Value
@Builder
public class OrderRejectedEvent {
    OrderId orderId;
    OrderStatus previousStatus;
    OrderStatus newStatus;
    String reason;
    Instant timestamp;
}