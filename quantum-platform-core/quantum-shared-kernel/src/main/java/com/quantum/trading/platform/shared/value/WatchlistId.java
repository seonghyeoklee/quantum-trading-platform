package com.quantum.trading.platform.shared.value;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.UUID;

/**
 * 관심종목 목록 식별자 Value Object
 */
public record WatchlistId(String value) {
    
    @JsonCreator
    public WatchlistId(@JsonProperty("value") String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("WatchlistId cannot be null or empty");
        }
        this.value = value.trim();
    }
    
    public static WatchlistId of(String value) {
        return new WatchlistId(value);
    }
    
    public static WatchlistId generate() {
        return new WatchlistId(UUID.randomUUID().toString());
    }
    
    @Override
    public String toString() {
        return value;
    }
}