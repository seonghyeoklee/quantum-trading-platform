package com.quantum.core.application.event;

import java.time.LocalDateTime;
import java.util.UUID;

/** Abstract base implementation for messages */
public abstract class AbstractMessage implements Message {

    private final String id;
    private final String correlationId;
    private final LocalDateTime timestamp;
    private final String type;
    private final int version;

    protected AbstractMessage(String correlationId) {
        this.id = UUID.randomUUID().toString();
        this.correlationId = correlationId != null ? correlationId : this.id;
        this.timestamp = LocalDateTime.now();
        this.type = this.getClass().getSimpleName();
        this.version = 1;
    }

    protected AbstractMessage(String id, String correlationId, LocalDateTime timestamp) {
        this.id = id;
        this.correlationId = correlationId;
        this.timestamp = timestamp;
        this.type = this.getClass().getSimpleName();
        this.version = 1;
    }

    @Override
    public String getId() {
        return id;
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
    public String getType() {
        return type;
    }

    @Override
    public int getVersion() {
        return version;
    }

    @Override
    public Object getData() {
        return this;
    }

    @Override
    public String toString() {
        return String.format(
                "%s{id='%s', correlationId='%s', timestamp=%s}",
                type, id, correlationId, timestamp);
    }
}
