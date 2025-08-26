package com.quantum.trading.platform.shared.value;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.UUID;

/**
 * 관심종목 그룹 식별자 Value Object
 */
public record WatchlistGroupId(String value) {
    
    @JsonCreator
    public WatchlistGroupId(@JsonProperty("value") String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("WatchlistGroupId cannot be null or empty");
        }
        this.value = value.trim();
    }
    
    public static WatchlistGroupId of(String value) {
        return new WatchlistGroupId(value);
    }
    
    public static WatchlistGroupId generate() {
        return new WatchlistGroupId(UUID.randomUUID().toString());
    }
    
    @Override
    public String toString() {
        return value;
    }
}