package com.quantum.trading.platform.shared.value;

import lombok.Value;

import java.util.UUID;

/**
 * 주문 식별자 Value Object
 * 
 * Axon Framework에서 Aggregate Identifier로 사용되는 주문 고유 식별자
 */
@Value
public class OrderId {
    String value;
    
    private OrderId(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("OrderId cannot be null or empty");
        }
        this.value = value;
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