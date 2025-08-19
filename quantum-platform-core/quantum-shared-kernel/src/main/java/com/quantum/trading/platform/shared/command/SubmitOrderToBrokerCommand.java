package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.OrderId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

/**
 * 주문 증권사 제출 명령
 * 
 * 검증이 완료된 주문을 증권사 API에 제출하기 위한 명령
 */
@Value
@Builder
public class SubmitOrderToBrokerCommand {
    @TargetAggregateIdentifier
    OrderId orderId;
    String brokerType;
    String accountNumber;
    
    public void validate() {
        if (orderId == null) {
            throw new IllegalArgumentException("OrderId is required");
        }
        if (brokerType == null || brokerType.trim().isEmpty()) {
            throw new IllegalArgumentException("BrokerType is required");
        }
        if (accountNumber == null || accountNumber.trim().isEmpty()) {
            throw new IllegalArgumentException("AccountNumber is required");
        }
    }
}