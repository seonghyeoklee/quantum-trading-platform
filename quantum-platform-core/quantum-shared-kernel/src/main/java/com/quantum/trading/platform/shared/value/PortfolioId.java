package com.quantum.trading.platform.shared.value;

import lombok.Value;

import java.util.UUID;

/**
 * 포트폴리오 식별자
 */
@Value
public class PortfolioId {
    String id;
    
    public static PortfolioId generate() {
        return new PortfolioId(UUID.randomUUID().toString());
    }
    
    public static PortfolioId of(String id) {
        if (id == null || id.trim().isEmpty()) {
            throw new IllegalArgumentException("Portfolio ID cannot be null or empty");
        }
        return new PortfolioId(id.trim());
    }
}