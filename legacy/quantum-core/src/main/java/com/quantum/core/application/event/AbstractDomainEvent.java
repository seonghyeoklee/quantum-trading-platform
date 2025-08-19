package com.quantum.core.application.event;

import java.time.LocalDateTime;

/** Abstract base implementation for domain events */
public abstract class AbstractDomainEvent extends AbstractMessage implements DomainEvent {

    private final String aggregateId;
    private final String aggregateType;
    private final int aggregateVersion;
    private final String triggeredBy;

    protected AbstractDomainEvent(
            String aggregateId,
            String aggregateType,
            int aggregateVersion,
            String triggeredBy,
            String correlationId) {
        super(correlationId);
        this.aggregateId = aggregateId;
        this.aggregateType = aggregateType;
        this.aggregateVersion = aggregateVersion;
        this.triggeredBy = triggeredBy;
    }

    protected AbstractDomainEvent(
            String id,
            String correlationId,
            LocalDateTime timestamp,
            String aggregateId,
            String aggregateType,
            int aggregateVersion,
            String triggeredBy) {
        super(id, correlationId, timestamp);
        this.aggregateId = aggregateId;
        this.aggregateType = aggregateType;
        this.aggregateVersion = aggregateVersion;
        this.triggeredBy = triggeredBy;
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
    public String toString() {
        return String.format(
                "%s{id='%s', aggregateId='%s', aggregateType='%s', version=%d, triggeredBy='%s', timestamp=%s}",
                getType(),
                getId(),
                aggregateId,
                aggregateType,
                aggregateVersion,
                triggeredBy,
                getTimestamp());
    }
}
