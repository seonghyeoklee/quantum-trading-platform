package com.quantum.core.application.state.stock;

import com.quantum.core.application.event.DomainEvent;
import com.quantum.core.application.event.stock.StockPriceUpdatedEvent;
import com.quantum.core.application.state.AggregateState;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/** Immutable stock aggregate state - Record implementation */
public record StockState(
        String aggregateId,
        String aggregateType,
        int version,
        String symbol,
        String name,
        String exchange,
        BigDecimal currentPrice,
        BigDecimal previousPrice,
        LocalDateTime lastUpdated,
        boolean active)
        implements AggregateState {

    /** Compact constructor with validation */
    public StockState {
        if (aggregateId == null || aggregateId.trim().isEmpty()) {
            throw new IllegalArgumentException("Aggregate ID cannot be null or empty");
        }
        if (aggregateType == null) {
            aggregateType = "Stock";
        }
        if (version < 0) {
            throw new IllegalArgumentException("Version cannot be negative");
        }
        if (currentPrice != null && currentPrice.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Current price cannot be negative");
        }
        if (previousPrice != null && previousPrice.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Previous price cannot be negative");
        }
    }

    /** Create an empty stock state */
    public static StockState empty(String aggregateId) {
        return new StockState(aggregateId, "Stock", 0, null, null, null, null, null, null, false);
    }

    /** Create a new stock state */
    public static StockState create(
            String aggregateId, String symbol, String name, String exchange) {
        return new StockState(
                aggregateId,
                "Stock",
                1,
                symbol,
                name,
                exchange,
                null,
                null,
                LocalDateTime.now(),
                true);
    }

    @Override
    public String getAggregateId() {
        return aggregateId;
    }

    @Override
    public String getAggregateType() {
        return aggregateType;
    }

    @Override
    public int getVersion() {
        return version;
    }

    @Override
    public AggregateState apply(DomainEvent event) {
        if (!canApply(event.getType())) {
            throw new IllegalArgumentException("Cannot apply event type: " + event.getType());
        }

        return switch (event.getType()) {
            case "StockPriceUpdatedEvent" -> applyStockPriceUpdated((StockPriceUpdatedEvent) event);
            default -> throw new IllegalArgumentException("Unknown event type: " + event.getType());
        };
    }

    @Override
    public boolean canApply(String eventType) {
        return "StockPriceUpdatedEvent".equals(eventType);
    }

    @Override
    public AggregateState createEmpty(String aggregateId) {
        return empty(aggregateId);
    }

    /** Apply stock price updated event */
    private StockState applyStockPriceUpdated(StockPriceUpdatedEvent event) {
        return new StockState(
                this.aggregateId,
                this.aggregateType,
                event.aggregateVersion(),
                this.symbol != null ? this.symbol : event.symbol(),
                this.name,
                this.exchange,
                event.newPrice(),
                event.previousPrice(),
                event.priceTimestamp(),
                true);
    }

    /** Update price (creates new state) */
    public StockState updatePrice(BigDecimal newPrice, LocalDateTime timestamp, int newVersion) {
        return new StockState(
                this.aggregateId,
                this.aggregateType,
                newVersion,
                this.symbol,
                this.name,
                this.exchange,
                newPrice,
                this.currentPrice, // current becomes previous
                timestamp,
                this.active);
    }

    /** Calculate price change amount */
    public BigDecimal priceChangeAmount() {
        if (currentPrice == null || previousPrice == null) {
            return BigDecimal.ZERO;
        }
        return currentPrice.subtract(previousPrice);
    }

    /** Calculate price change percentage */
    public BigDecimal priceChangePercentage() {
        if (currentPrice == null
                || previousPrice == null
                || previousPrice.compareTo(BigDecimal.ZERO) == 0) {
            return BigDecimal.ZERO;
        }
        return priceChangeAmount()
                .divide(previousPrice, 4, java.math.RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));
    }

    /** Check if price increased */
    public boolean isPriceIncrease() {
        return priceChangeAmount().compareTo(BigDecimal.ZERO) > 0;
    }

    /** Check if price decreased */
    public boolean isPriceDecrease() {
        return priceChangeAmount().compareTo(BigDecimal.ZERO) < 0;
    }

    /** Check if state is initialized */
    public boolean isInitialized() {
        return symbol != null && !symbol.trim().isEmpty();
    }
}
