package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.OrderId;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 주문 증권사 제출 이벤트
 * 
 * 주문이 증권사 API에 제출되었을 때 발행되는 이벤트
 */
@Value
@Builder
public class OrderSubmittedToBrokerEvent {
    OrderId orderId;
    String brokerType;
    String brokerOrderId;
    Instant submittedAt;
    
    public static OrderSubmittedToBrokerEvent create(
            OrderId orderId,
            String brokerType,
            String brokerOrderId) {
        return OrderSubmittedToBrokerEvent.builder()
                .orderId(orderId)
                .brokerType(brokerType)
                .brokerOrderId(brokerOrderId)
                .submittedAt(Instant.now())
                .build();
    }
}