package com.quantum.core.infrastructure.eventsourcing;

import com.quantum.core.application.event.DomainEvent;
import com.quantum.core.application.state.AggregateState;
import com.quantum.core.domain.port.eventsourcing.EventStore;
import java.util.List;
import java.util.Optional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/** Service for rehydrating aggregate state from event streams */
@Component
public class StateRehydrator {

    private static final Logger logger = LoggerFactory.getLogger(StateRehydrator.class);

    private final EventStore eventStore;

    public StateRehydrator(EventStore eventStore) {
        this.eventStore = eventStore;
    }

    /** Rehydrate aggregate state from all events in the stream */
    public <T extends AggregateState> Optional<T> rehydrate(String streamId, T initialState) {
        logger.debug("Rehydrating state for stream: {}", streamId);

        if (!eventStore.streamExists(streamId)) {
            logger.debug("Stream does not exist: {}", streamId);
            return Optional.empty();
        }

        List<DomainEvent> events = eventStore.readStream(streamId);
        if (events.isEmpty()) {
            logger.debug("No events found for stream: {}", streamId);
            return Optional.empty();
        }

        T state = initialState;
        for (DomainEvent event : events) {
            try {
                state = (T) state.apply(event);
                logger.trace("Applied event {} to state for stream: {}", event.getType(), streamId);
            } catch (Exception e) {
                logger.error(
                        "Failed to apply event {} to state for stream: {}",
                        event.getType(),
                        streamId,
                        e);
                throw new StateRehydrationException(
                        String.format(
                                "Failed to apply event %s to state for stream %s",
                                event.getType(), streamId),
                        e);
            }
        }

        logger.debug(
                "Successfully rehydrated state for stream: {} with {} events",
                streamId,
                events.size());
        return Optional.of(state);
    }

    /** Rehydrate aggregate state from events starting from a specific version */
    public <T extends AggregateState> Optional<T> rehydrate(
            String streamId, T initialState, int fromVersion) {
        logger.debug("Rehydrating state for stream: {} from version: {}", streamId, fromVersion);

        if (!eventStore.streamExists(streamId)) {
            logger.debug("Stream does not exist: {}", streamId);
            return Optional.empty();
        }

        List<DomainEvent> events = eventStore.readStream(streamId, fromVersion);
        if (events.isEmpty()) {
            logger.debug("No events found for stream: {} from version: {}", streamId, fromVersion);
            return Optional.of(initialState);
        }

        T state = initialState;
        for (DomainEvent event : events) {
            try {
                state = (T) state.apply(event);
                logger.trace("Applied event {} to state for stream: {}", event.getType(), streamId);
            } catch (Exception e) {
                logger.error(
                        "Failed to apply event {} to state for stream: {}",
                        event.getType(),
                        streamId,
                        e);
                throw new StateRehydrationException(
                        String.format(
                                "Failed to apply event %s to state for stream %s",
                                event.getType(), streamId),
                        e);
            }
        }

        logger.debug(
                "Successfully rehydrated state for stream: {} from version: {} with {} events",
                streamId,
                fromVersion,
                events.size());
        return Optional.of(state);
    }

    /** Rehydrate aggregate state up to a specific version */
    public <T extends AggregateState> Optional<T> rehydrateToVersion(
            String streamId, T initialState, int toVersion) {
        logger.debug("Rehydrating state for stream: {} to version: {}", streamId, toVersion);

        if (!eventStore.streamExists(streamId)) {
            logger.debug("Stream does not exist: {}", streamId);
            return Optional.empty();
        }

        List<DomainEvent> events = eventStore.readStreamToVersion(streamId, toVersion);
        if (events.isEmpty()) {
            logger.debug("No events found for stream: {} to version: {}", streamId, toVersion);
            return Optional.empty();
        }

        T state = initialState;
        for (DomainEvent event : events) {
            try {
                state = (T) state.apply(event);
                logger.trace("Applied event {} to state for stream: {}", event.getType(), streamId);
            } catch (Exception e) {
                logger.error(
                        "Failed to apply event {} to state for stream: {}",
                        event.getType(),
                        streamId,
                        e);
                throw new StateRehydrationException(
                        String.format(
                                "Failed to apply event %s to state for stream %s",
                                event.getType(), streamId),
                        e);
            }
        }

        logger.debug(
                "Successfully rehydrated state for stream: {} to version: {} with {} events",
                streamId,
                toVersion,
                events.size());
        return Optional.of(state);
    }

    /** Get the current version of a stream */
    public Optional<Integer> getStreamVersion(String streamId) {
        return eventStore.getStreamVersion(streamId);
    }

    /** Check if a stream exists */
    public boolean streamExists(String streamId) {
        return eventStore.streamExists(streamId);
    }

    /** Exception thrown when state rehydration fails */
    public static class StateRehydrationException extends RuntimeException {
        public StateRehydrationException(String message) {
            super(message);
        }

        public StateRehydrationException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
