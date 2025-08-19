package com.quantum.trading.platform.shared.value;

import lombok.Value;

/**
 * 사용자 식별자 Value Object
 */
@Value
public class UserId {
    String value;
    
    private UserId(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("UserId cannot be null or empty");
        }
        this.value = value;
    }
    
    public static UserId of(String value) {
        return new UserId(value);
    }
    
    @Override
    public String toString() {
        return value;
    }
}