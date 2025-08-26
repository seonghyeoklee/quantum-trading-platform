package com.quantum.trading.platform.shared.value;

import java.util.UUID;

/**
 * 주문 식별자 Value Object (Record 타입)
 * 
 * Axon Framework에서 Aggregate Identifier로 사용되는 주문 고유 식별자
 */
public record OrderId(String value) {
    
    public OrderId {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("OrderId cannot be null or empty");
        }
        value = value.trim();
    }
    
    public static OrderId of(String value) {
        return new OrderId(value);
    }
    
    public static OrderId generate() {
        return new OrderId("ORDER-" + UUID.randomUUID().toString());
    }
    
    @Override
    public String toString() {
        return value;
    }
}