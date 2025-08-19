package com.quantum.core.domain.port.eventsourcing;

import com.quantum.core.application.event.DomainEvent;
import java.util.List;
import java.util.Optional;

/** Event Store interface for persisting and retrieving events */
public interface EventStore {

    /**
     * Append events to a stream with optimistic concurrency control
     *
     * @param streamId the stream identifier
     * @param expectedVersion expected version for optimistic locking
     * @param events events to append
     * @throws ConcurrencyException if expected version doesn't match
     */
    void appendEvents(String streamId, int expectedVersion, List<DomainEvent> events);

    /**
     * Read all events from a stream
     *
     * @param streamId the stream identifier
     * @return list of events in order
     */
    List<DomainEvent> readStream(String streamId);

    /**
     * Read events from a stream starting from a specific version
     *
     * @param streamId the stream identifier
     * @param fromVersion starting version (inclusive)
     * @return list of events from the specified version
     */
    List<DomainEvent> readStream(String streamId, int fromVersion);

    /**
     * Read events from a stream up to a specific version
     *
     * @param streamId the stream identifier
     * @param toVersion ending version (inclusive)
     * @return list of events up to the specified version
     */
    List<DomainEvent> readStreamToVersion(String streamId, int toVersion);

    /**
     * Get the current version of a stream
     *
     * @param streamId the stream identifier
     * @return current version, or empty if stream doesn't exist
     */
    Optional<Integer> getStreamVersion(String streamId);

    /**
     * Check if a stream exists
     *
     * @param streamId the stream identifier
     * @return true if stream exists
     */
    boolean streamExists(String streamId);

    /**
     * Subscribe to events matching a pattern
     *
     * @param streamPattern pattern to match (e.g., "order-*", "stock-*")
     * @param handler event handler
     */
    void subscribe(String streamPattern, EventHandler handler);

    /**
     * Get all events of a specific type across all streams
     *
     * @param eventType the event type to filter by
     * @return list of matching events
     */
    List<DomainEvent> getEventsByType(String eventType);

    /** Simple event handler interface for event store subscriptions */
    interface EventHandler {
        /**
         * Handle an event
         *
         * @param event the event to handle
         */
        void handle(DomainEvent event);

        /**
         * Check if this handler can handle the given event type
         *
         * @param eventType the event type to check
         * @return true if this handler can handle the event type
         */
        default boolean canHandle(String eventType) {
            return true; // By default, handle all events
        }
    }

    /** Exception thrown when optimistic concurrency check fails */
    class ConcurrencyException extends RuntimeException {
        public ConcurrencyException(String message) {
            super(message);
        }
    }
}
