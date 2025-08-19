package com.quantum.core.application.event;

import java.time.LocalDateTime;
import java.util.UUID;

/** Generic message wrapper for commands and events */
public class MessageWrapper<T> implements Message {

    private final String id;
    private final String correlationId;
    private final LocalDateTime timestamp;
    private final String type;
    private final T payload;
    private final int version;

    private MessageWrapper(
            String id,
            String correlationId,
            LocalDateTime timestamp,
            String type,
            T payload,
            int version) {
        this.id = id;
        this.correlationId = correlationId;
        this.timestamp = timestamp;
        this.type = type;
        this.payload = payload;
        this.version = version;
    }

    /** Create a new message wrapper with the given payload */
    public static <T> MessageWrapper<T> of(T payload) {
        return new MessageWrapper<>(
                UUID.randomUUID().toString(),
                UUID.randomUUID().toString(),
                LocalDateTime.now(),
                payload.getClass().getSimpleName(),
                payload,
                1);
    }

    /** Create a new message wrapper with the given payload and correlation ID */
    public static <T> MessageWrapper<T> of(T payload, String correlationId) {
        return new MessageWrapper<>(
                UUID.randomUUID().toString(),
                correlationId,
                LocalDateTime.now(),
                payload.getClass().getSimpleName(),
                payload,
                1);
    }

    /** Create a message wrapper from existing message properties */
    public static <T> MessageWrapper<T> from(
            String id, String correlationId, LocalDateTime timestamp, T payload) {
        return new MessageWrapper<>(
                id, correlationId, timestamp, payload.getClass().getSimpleName(), payload, 1);
    }

    /** Get the wrapped payload */
    public T getPayload() {
        return payload;
    }

    /** Get the command from the payload (assumes payload is a StreamCommand) */
    @SuppressWarnings("unchecked")
    public T getCommand() {
        return payload;
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
    public Object getData() {
        return payload;
    }

    @Override
    public int getVersion() {
        return version;
    }

    @Override
    public String toString() {
        return String.format(
                "MessageWrapper{id='%s', correlationId='%s', type='%s', timestamp=%s, payload=%s}",
                id, correlationId, type, timestamp, payload);
    }
}
