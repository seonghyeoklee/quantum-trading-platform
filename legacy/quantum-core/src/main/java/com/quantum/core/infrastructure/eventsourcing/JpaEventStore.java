package com.quantum.core.infrastructure.eventsourcing;

import com.quantum.core.application.event.DomainEvent;
import com.quantum.core.domain.port.eventsourcing.EventSerializer;
import com.quantum.core.domain.port.eventsourcing.EventStore;
import com.quantum.core.infrastructure.persistence.EventStoreEntity;
import com.quantum.core.infrastructure.persistence.EventStoreRepository;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/** JPA-based EventStore implementation */
@Component
@Transactional
public class JpaEventStore implements EventStore {

    private static final Logger logger = LoggerFactory.getLogger(JpaEventStore.class);

    private final EventStoreRepository eventStoreRepository;
    private final EventSerializer eventSerializer;
    private final Map<String, List<EventStore.EventHandler>> subscribers;

    public JpaEventStore(
            EventStoreRepository eventStoreRepository, EventSerializer eventSerializer) {
        this.eventStoreRepository = eventStoreRepository;
        this.eventSerializer = eventSerializer;
        this.subscribers = new ConcurrentHashMap<>();
    }

    @Override
    public void appendEvents(String streamId, int expectedVersion, List<DomainEvent> events) {
        if (events == null || events.isEmpty()) {
            return;
        }

        logger.debug(
                "Appending {} events to stream: {}, expectedVersion: {}",
                events.size(),
                streamId,
                expectedVersion);

        // Check for concurrency conflicts
        if (expectedVersion >= 0) {
            checkConcurrency(streamId, expectedVersion);
        }

        // Convert events to entities and save
        List<EventStoreEntity> entities =
                events.stream()
                        .map(event -> toEntity(event, streamId))
                        .collect(Collectors.toList());

        try {
            eventStoreRepository.saveAll(entities);
            logger.info("Successfully appended {} events to stream: {}", events.size(), streamId);

            // Notify subscribers
            notifySubscribers(events);

        } catch (Exception e) {
            logger.error("Failed to append events to stream: {}", streamId, e);
            throw new EventStoreException("Failed to append events", e);
        }
    }

    @Override
    @Transactional(readOnly = true)
    public List<DomainEvent> readStream(String streamId) {
        logger.debug("Reading all events from stream: {}", streamId);

        List<EventStoreEntity> entities =
                eventStoreRepository.findByStreamIdOrderByVersionAsc(streamId);
        return entities.stream().map(this::fromEntity).collect(Collectors.toList());
    }

    @Override
    @Transactional(readOnly = true)
    public List<DomainEvent> readStream(String streamId, int fromVersion) {
        logger.debug(
                "Reading events from stream: {} starting from version: {}", streamId, fromVersion);

        List<EventStoreEntity> entities =
                eventStoreRepository.findByStreamIdFromVersion(streamId, fromVersion);
        return entities.stream().map(this::fromEntity).collect(Collectors.toList());
    }

    @Override
    @Transactional(readOnly = true)
    public List<DomainEvent> readStreamToVersion(String streamId, int toVersion) {
        logger.debug("Reading events from stream: {} up to version: {}", streamId, toVersion);

        List<EventStoreEntity> entities =
                eventStoreRepository.findByStreamIdToVersion(streamId, toVersion);
        return entities.stream().map(this::fromEntity).collect(Collectors.toList());
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<Integer> getStreamVersion(String streamId) {
        return eventStoreRepository.findMaxVersionByStreamId(streamId);
    }

    @Override
    @Transactional(readOnly = true)
    public boolean streamExists(String streamId) {
        return eventStoreRepository.existsByStreamId(streamId);
    }

    @Override
    public void subscribe(String streamPattern, EventStore.EventHandler handler) {
        subscribers.computeIfAbsent(streamPattern, k -> new ArrayList<>()).add(handler);
        logger.info("Subscribed handler to pattern: {}", streamPattern);
    }

    @Override
    @Transactional(readOnly = true)
    public List<DomainEvent> getEventsByType(String eventType) {
        logger.debug("Reading all events of type: {}", eventType);

        List<EventStoreEntity> entities =
                eventStoreRepository.findByEventTypeOrderByCreatedAtAsc(eventType);
        return entities.stream().map(this::fromEntity).collect(Collectors.toList());
    }

    private void checkConcurrency(String streamId, int expectedVersion) {
        Optional<Integer> currentVersion = getStreamVersion(streamId);

        if (currentVersion.isPresent() && !currentVersion.get().equals(expectedVersion)) {
            throw new ConcurrencyException(
                    String.format(
                            "Concurrency conflict in stream %s. Expected version: %d, actual version: %d",
                            streamId, expectedVersion, currentVersion.get()));
        }

        if (currentVersion.isEmpty() && expectedVersion != 0) {
            throw new ConcurrencyException(
                    String.format(
                            "Concurrency conflict in stream %s. Expected version: %d, but stream doesn't exist",
                            streamId, expectedVersion));
        }
    }

    private EventStoreEntity toEntity(DomainEvent event, String streamId) {
        String eventData = eventSerializer.serialize(event);
        String metadata = eventSerializer.createMetadata(event);

        return new EventStoreEntity(
                event.getId(),
                streamId,
                event.getAggregateVersion(),
                event.getType(),
                event.getAggregateType(),
                event.getAggregateId(),
                event.getCorrelationId(),
                event.getTriggeredBy(),
                eventData,
                metadata);
    }

    private DomainEvent fromEntity(EventStoreEntity entity) {
        try {
            return eventSerializer.deserialize(entity.getEventData(), entity.getEventType());
        } catch (Exception e) {
            logger.error("Failed to deserialize event from entity: {}", entity, e);
            throw new EventStoreException("Failed to deserialize event", e);
        }
    }

    private void notifySubscribers(List<DomainEvent> events) {
        for (DomainEvent event : events) {
            for (Map.Entry<String, List<EventStore.EventHandler>> entry : subscribers.entrySet()) {
                String pattern = entry.getKey();
                if (matchesPattern(event.getAggregateId(), pattern)) {
                    for (EventStore.EventHandler handler : entry.getValue()) {
                        try {
                            if (handler.canHandle(event.getType())) {
                                handler.handle(event);
                            }
                        } catch (Exception e) {
                            logger.error(
                                    "Error in event handler for pattern: {}, event: {}",
                                    pattern,
                                    event,
                                    e);
                        }
                    }
                }
            }
        }
    }

    private boolean matchesPattern(String streamId, String pattern) {
        if ("*".equals(pattern)) {
            return true;
        }

        if (pattern.endsWith("*")) {
            String prefix = pattern.substring(0, pattern.length() - 1);
            return streamId.startsWith(prefix);
        }

        return streamId.equals(pattern);
    }

    /** Exception thrown when event store operations fail */
    public static class EventStoreException extends RuntimeException {
        public EventStoreException(String message) {
            super(message);
        }

        public EventStoreException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
