package com.quantum.trading.platform.shared.value;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * 사용자 식별자 Value Object (Record 타입)
 */
public record UserId(String value) {
    
    @JsonCreator
    public UserId(@JsonProperty("value") String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("UserId cannot be null or empty");
        }
        this.value = value.trim();
    }
    
    public static UserId of(String value) {
        return new UserId(value);
    }
    
    @Override
    public String toString() {
        return value;
    }
}