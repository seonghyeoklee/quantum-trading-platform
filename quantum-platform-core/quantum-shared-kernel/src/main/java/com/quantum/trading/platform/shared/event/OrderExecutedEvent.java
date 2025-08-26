package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.Money;
import com.quantum.trading.platform.shared.value.OrderId;
import com.quantum.trading.platform.shared.value.Quantity;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 주문 체결 이벤트
 * 
 * 주문이 전부 또는 부분 체결되었을 때 발행되는 이벤트
 */
@Value
@Builder
public class OrderExecutedEvent {
    OrderId orderId;
    Money executedPrice;
    Quantity executedQuantity;
    Quantity remainingQuantity;
    String brokerOrderId;
    String executionId;
    Instant executedAt;
    boolean isFullyExecuted;
    
    public static OrderExecutedEvent create(
            OrderId orderId,
            Money executedPrice,
            Quantity executedQuantity,
            Quantity remainingQuantity,
            String brokerOrderId,
            String executionId) {
        return OrderExecutedEvent.builder()
                .orderId(orderId)
                .executedPrice(executedPrice)
                .executedQuantity(executedQuantity)
                .remainingQuantity(remainingQuantity)
                .brokerOrderId(brokerOrderId)
                .executionId(executionId)
                .executedAt(Instant.now())
                .isFullyExecuted(remainingQuantity.value() == 0)
                .build();
    }
}