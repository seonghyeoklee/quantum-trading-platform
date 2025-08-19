package com.quantum.core.domain.port.eventsourcing;

import com.quantum.core.application.event.DomainEvent;

/** Interface for serializing and deserializing events */
public interface EventSerializer {

    /**
     * Serialize an event to string format (usually JSON)
     *
     * @param event the event to serialize
     * @return serialized event data
     */
    String serialize(DomainEvent event);

    /**
     * Deserialize an event from string format
     *
     * @param eventData the serialized event data
     * @param eventType the event type
     * @return deserialized event
     */
    DomainEvent deserialize(String eventData, String eventType);

    /**
     * Create metadata for an event
     *
     * @param event the event
     * @return metadata as string
     */
    String createMetadata(DomainEvent event);
}
