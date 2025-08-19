package com.quantum.core.infrastructure.eventsourcing;

import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.quantum.core.application.event.DomainEvent;
import com.quantum.core.domain.port.eventsourcing.EventSerializer;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/** JSON-based event serializer with automatic type handling */
@Component
public class JsonEventSerializer implements EventSerializer {

    private static final Logger logger = LoggerFactory.getLogger(JsonEventSerializer.class);

    private final ObjectMapper objectMapper;

    public JsonEventSerializer() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());

        // Jackson polymorphic type handling
        this.objectMapper.activateDefaultTyping(
                this.objectMapper.getPolymorphicTypeValidator(),
                ObjectMapper.DefaultTyping.NON_FINAL,
                JsonTypeInfo.As.PROPERTY);
    }

    @Override
    public String serialize(DomainEvent event) {
        try {
            EventWrapper wrapper = new EventWrapper(event.getClass().getSimpleName(), event);
            return objectMapper.writeValueAsString(wrapper);
        } catch (JsonProcessingException e) {
            logger.error("Failed to serialize event: {}", event, e);
            throw new SerializationException("Failed to serialize event", e);
        }
    }

    @Override
    public DomainEvent deserialize(String eventData, String eventType) {
        try {
            EventWrapper wrapper = objectMapper.readValue(eventData, EventWrapper.class);
            return wrapper.getEvent();
        } catch (JsonProcessingException e) {
            logger.error(
                    "Failed to deserialize event data: {} of type: {}", eventData, eventType, e);
            throw new SerializationException("Failed to deserialize event", e);
        }
    }

    @Override
    public String createMetadata(DomainEvent event) {
        try {
            Map<String, Object> metadata = new HashMap<>();
            metadata.put("serializedAt", LocalDateTime.now());
            metadata.put("serializerVersion", "2.0");
            metadata.put("eventTypeVersion", event.getVersion());
            metadata.put("eventClass", event.getClass().getName());

            return objectMapper.writeValueAsString(metadata);
        } catch (JsonProcessingException e) {
            logger.error("Failed to create metadata for event: {}", event, e);
            throw new SerializationException("Failed to create metadata", e);
        }
    }

    /** Wrapper class for polymorphic serialization */
    public static class EventWrapper {
        private String eventType;
        private DomainEvent event;

        public EventWrapper() {}

        public EventWrapper(String eventType, DomainEvent event) {
            this.eventType = eventType;
            this.event = event;
        }

        public String getEventType() {
            return eventType;
        }

        public void setEventType(String eventType) {
            this.eventType = eventType;
        }

        public DomainEvent getEvent() {
            return event;
        }

        public void setEvent(DomainEvent event) {
            this.event = event;
        }
    }

    /** Exception thrown when serialization/deserialization fails */
    public static class SerializationException extends RuntimeException {
        public SerializationException(String message) {
            super(message);
        }

        public SerializationException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
