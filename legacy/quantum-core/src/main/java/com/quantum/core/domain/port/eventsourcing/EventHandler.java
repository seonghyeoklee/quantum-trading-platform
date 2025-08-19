package com.quantum.core.domain.port.eventsourcing;

import com.quantum.core.application.event.DomainEvent;
import com.quantum.core.application.state.AggregateState;
import java.util.List;

/**
 * Interface for handling events and applying them to aggregate state Used for state rehydration
 * from event streams
 *
 * @param <T> the aggregate state type this handler operates on
 */
public interface EventHandler<T extends AggregateState> {

    /**
     * Apply a single event to the current state
     *
     * @param currentState the current state of the aggregate
     * @param event the event to apply
     * @return the new state after applying the event
     */
    T apply(T currentState, DomainEvent event);

    /**
     * Apply multiple events to the current state in sequence
     *
     * @param currentState the current state of the aggregate
     * @param events the events to apply in order
     * @return the new state after applying all events
     */
    default T applyAll(T currentState, List<DomainEvent> events) {
        T state = currentState;
        for (DomainEvent event : events) {
            state = apply(state, event);
        }
        return state;
    }

    /**
     * Check if this handler can handle the given event type
     *
     * @param eventType the event type to check
     * @return true if this handler can handle the event type
     */
    boolean canHandle(String eventType);

    /**
     * Check if this handler can handle the given event
     *
     * @param event the event to check
     * @return true if this handler can handle the event
     */
    default boolean canHandle(DomainEvent event) {
        return canHandle(event.getClass().getSimpleName());
    }

    /**
     * Get the aggregate type this handler operates on
     *
     * @return the aggregate type name
     */
    default String getAggregateType() {
        return "Unknown";
    }

    /**
     * Get the initial state for a new aggregate
     *
     * @param streamId the stream identifier
     * @return the initial state for the aggregate
     */
    T getInitialState(String streamId);

    /**
     * Validate an event before applying it
     *
     * @param event the event to validate
     * @param currentState the current aggregate state
     * @throws EventValidationException if the event is invalid
     */
    default void validate(DomainEvent event, T currentState) throws EventValidationException {
        // Default implementation - no validation
    }

    /**
     * Hook called before applying an event Can be used for logging, metrics, etc.
     *
     * @param event the event about to be applied
     * @param currentState the current state
     */
    default void beforeApply(DomainEvent event, T currentState) {
        // Default implementation - do nothing
    }

    /**
     * Hook called after applying an event Can be used for logging, metrics, etc.
     *
     * @param event the event that was applied
     * @param previousState the state before applying the event
     * @param newState the state after applying the event
     */
    default void afterApply(DomainEvent event, T previousState, T newState) {
        // Default implementation - do nothing
    }

    /** Exception thrown when event validation fails */
    class EventValidationException extends RuntimeException {
        public EventValidationException(String message) {
            super(message);
        }

        public EventValidationException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
