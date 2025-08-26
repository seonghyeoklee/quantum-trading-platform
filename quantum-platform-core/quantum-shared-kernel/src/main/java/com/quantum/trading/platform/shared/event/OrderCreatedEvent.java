package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.*;

import java.time.Instant;

/**
 * 주문 생성 이벤트
 * 
 * 새로운 주문이 생성되었을 때 발행되는 도메인 이벤트
 * Axon Framework에서 Event Sourcing의 핵심 이벤트
 */
public record OrderCreatedEvent(
    OrderId orderId,
    UserId userId,
    Symbol symbol,
    OrderType orderType,
    OrderSide side,
    Money price,
    Quantity quantity,
    Instant timestamp
) {
    
    public static OrderCreatedEvent create(
            OrderId orderId,
            UserId userId,
            Symbol symbol,
            OrderType orderType,
            OrderSide side,
            Money price,
            Quantity quantity) {
        return new OrderCreatedEvent(
                orderId,
                userId,
                symbol,
                orderType,
                side,
                price,
                quantity,
                Instant.now());
    }
}