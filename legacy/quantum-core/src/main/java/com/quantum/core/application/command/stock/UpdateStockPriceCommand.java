package com.quantum.core.application.command.stock;

import com.quantum.core.application.command.StreamCommand;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

/** Command to update stock price - immutable record */
public record UpdateStockPriceCommand(
        String id,
        String streamId,
        int expectedVersion,
        String correlationId,
        LocalDateTime timestamp,
        String symbol,
        BigDecimal newPrice,
        LocalDateTime priceTimestamp,
        String source)
        implements StreamCommand {

    /** Compact constructor with validation */
    public UpdateStockPriceCommand {
        // Validation in compact constructor
        if (id == null || id.trim().isEmpty()) {
            id = UUID.randomUUID().toString();
        }
        if (streamId == null || streamId.trim().isEmpty()) {
            throw new IllegalArgumentException("Stream ID cannot be null or empty");
        }
        if (timestamp == null) {
            timestamp = LocalDateTime.now();
        }
        if (symbol == null || symbol.trim().isEmpty()) {
            throw new IllegalArgumentException("Symbol cannot be null or empty");
        }
        if (newPrice == null) {
            throw new IllegalArgumentException("New price cannot be null");
        }
        if (newPrice.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("New price must be positive");
        }
        if (priceTimestamp == null) {
            throw new IllegalArgumentException("Price timestamp cannot be null");
        }
        if (source == null || source.trim().isEmpty()) {
            throw new IllegalArgumentException("Source cannot be null or empty");
        }
    }

    /** Convenience constructor for most common use case */
    public UpdateStockPriceCommand(
            String stockId,
            String symbol,
            BigDecimal newPrice,
            LocalDateTime priceTimestamp,
            String source) {
        this(null, stockId, -1, null, null, symbol, newPrice, priceTimestamp, source);
    }

    /** Constructor with expected version */
    public UpdateStockPriceCommand(
            String stockId,
            String symbol,
            BigDecimal newPrice,
            LocalDateTime priceTimestamp,
            String source,
            int expectedVersion,
            String correlationId) {
        this(
                null,
                stockId,
                expectedVersion,
                correlationId,
                null,
                symbol,
                newPrice,
                priceTimestamp,
                source);
    }

    @Override
    public String getType() {
        return this.getClass().getSimpleName();
    }

    @Override
    public String getId() {
        return id;
    }

    @Override
    public String getStreamId() {
        return streamId;
    }

    @Override
    public int getExpectedVersion() {
        return expectedVersion;
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

    @Override
    public void validate() {
        // Validation is already done in compact constructor
        // This method is kept for interface compatibility
    }
}
