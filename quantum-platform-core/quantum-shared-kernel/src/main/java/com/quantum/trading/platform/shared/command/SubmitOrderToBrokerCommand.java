package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.OrderId;
import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;
import lombok.Builder;

import java.time.Instant;

/**
 * 주문 증권사 제출 명령
 * 
 * 검증이 완료된 주문을 증권사 API에 제출하기 위한 명령
 */
@Builder
public record SubmitOrderToBrokerCommand(
    @TargetAggregateIdentifier
    OrderId orderId,
    UserId userId,
    String brokerType,
    String brokerOrderId,
    Instant submittedAt
) {
    
    public void validate() {
        if (orderId == null) {
            throw new IllegalArgumentException("OrderId is required");
        }
        if (userId == null) {
            throw new IllegalArgumentException("UserId is required");
        }
        if (brokerType == null || brokerType.trim().isEmpty()) {
            throw new IllegalArgumentException("BrokerType is required");
        }
        if (brokerOrderId == null || brokerOrderId.trim().isEmpty()) {
            throw new IllegalArgumentException("BrokerOrderId is required");
        }
        if (submittedAt == null) {
            throw new IllegalArgumentException("SubmittedAt is required");
        }
    }
}