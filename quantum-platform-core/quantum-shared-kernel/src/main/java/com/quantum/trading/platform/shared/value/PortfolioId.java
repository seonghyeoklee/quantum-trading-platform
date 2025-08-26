package com.quantum.trading.platform.shared.value;

import java.util.UUID;

/**
 * 포트폴리오 식별자 (Record 타입)
 */
public record PortfolioId(String id) {
    
    public PortfolioId {
        if (id == null || id.trim().isEmpty()) {
            throw new IllegalArgumentException("Portfolio ID cannot be null or empty");
        }
        id = id.trim();
    }
    
    public static PortfolioId generate() {
        return new PortfolioId(UUID.randomUUID().toString());
    }
    
    public static PortfolioId of(String id) {
        return new PortfolioId(id);
    }
    
    @Override
    public String toString() {
        return id;
    }
}