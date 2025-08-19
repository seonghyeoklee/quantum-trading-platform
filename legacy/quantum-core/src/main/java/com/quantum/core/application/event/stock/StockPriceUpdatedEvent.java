package com.quantum.core.application.event.stock;

import com.quantum.core.application.event.DomainEvent;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.UUID;

/** Event fired when a stock price is updated - immutable record */
public record StockPriceUpdatedEvent(
        String id,
        String aggregateId,
        String aggregateType,
        int aggregateVersion,
        String triggeredBy,
        String correlationId,
        LocalDateTime timestamp,
        String symbol,
        BigDecimal previousPrice,
        BigDecimal newPrice,
        LocalDateTime priceTimestamp)
        implements DomainEvent {

    /** Compact constructor with validation and derived calculations */
    public StockPriceUpdatedEvent {
        if (id == null || id.trim().isEmpty()) {
            id = UUID.randomUUID().toString();
        }
        if (aggregateId == null || aggregateId.trim().isEmpty()) {
            throw new IllegalArgumentException("Aggregate ID cannot be null or empty");
        }
        if (aggregateType == null) {
            aggregateType = "Stock";
        }
        if (timestamp == null) {
            timestamp = LocalDateTime.now();
        }
        if (symbol == null || symbol.trim().isEmpty()) {
            throw new IllegalArgumentException("Symbol cannot be null or empty");
        }
        if (previousPrice == null) {
            throw new IllegalArgumentException("Previous price cannot be null");
        }
        if (newPrice == null) {
            throw new IllegalArgumentException("New price cannot be null");
        }
        if (priceTimestamp == null) {
            throw new IllegalArgumentException("Price timestamp cannot be null");
        }
    }

    /** Convenience constructor for most common use case */
    public StockPriceUpdatedEvent(
            String stockId,
            String symbol,
            BigDecimal previousPrice,
            BigDecimal newPrice,
            int aggregateVersion,
            String triggeredBy,
            String correlationId,
            LocalDateTime priceTimestamp) {
        this(
                null,
                stockId,
                "Stock",
                aggregateVersion,
                triggeredBy,
                correlationId,
                null,
                symbol,
                previousPrice,
                newPrice,
                priceTimestamp);
    }

    @Override
    public String getType() {
        return this.getClass().getSimpleName();
    }

    @Override
    public int getVersion() {
        return 1; // Event schema version
    }

    @Override
    public String getId() {
        return id;
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
    public int getAggregateVersion() {
        return aggregateVersion;
    }

    @Override
    public String getTriggeredBy() {
        return triggeredBy;
    }

    @Override
    public String getCorrelationId() {
        return correlationId;
    }

    @Override
    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    @Override
    public Object getData() {
        return this; // Record itself is the data
    }

    /** Calculate the price change amount */
    public BigDecimal changeAmount() {
        return newPrice.subtract(previousPrice);
    }

    /** Calculate the price change percentage */
    public BigDecimal changePercentage() {
        if (previousPrice.compareTo(BigDecimal.ZERO) == 0) {
            return BigDecimal.ZERO;
        }
        return changeAmount()
                .divide(previousPrice, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));
    }

    /** Check if price increased */
    public boolean isPriceIncrease() {
        return changeAmount().compareTo(BigDecimal.ZERO) > 0;
    }

    /** Check if price decreased */
    public boolean isPriceDecrease() {
        return changeAmount().compareTo(BigDecimal.ZERO) < 0;
    }

    /** Check if price unchanged */
    public boolean isPriceUnchanged() {
        return changeAmount().compareTo(BigDecimal.ZERO) == 0;
    }
}
