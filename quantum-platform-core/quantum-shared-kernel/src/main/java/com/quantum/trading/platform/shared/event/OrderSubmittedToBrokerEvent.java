package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.OrderId;
import com.quantum.trading.platform.shared.value.UserId;

import java.time.Instant;

/**
 * 주문 증권사 제출 이벤트
 * 
 * 주문이 증권사 API에 제출되었을 때 발행되는 이벤트
 */
public record OrderSubmittedToBrokerEvent(
    OrderId orderId,
    UserId userId,
    String brokerType,
    String brokerOrderId,
    Instant submittedAt
) {
    
    public static OrderSubmittedToBrokerEvent create(
            OrderId orderId,
            UserId userId,
            String brokerType,
            String brokerOrderId) {
        return new OrderSubmittedToBrokerEvent(
                orderId,
                userId,
                brokerType,
                brokerOrderId,
                Instant.now());
    }
}