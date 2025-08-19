package com.quantum.core.application.state;

import com.quantum.core.application.event.DomainEvent;

/** Base interface for aggregate states */
public interface AggregateState {

    /** Get the aggregate identifier */
    String getAggregateId();

    /** Get the aggregate type */
    String getAggregateType();

    /** Get the current version of this aggregate */
    int getVersion();

    /**
     * Apply an event to this state to produce a new state This method should be pure (no side
     * effects)
     *
     * @param event the event to apply
     * @return new state after applying the event
     */
    AggregateState apply(DomainEvent event);

    /**
     * Check if this state can handle the given event type
     *
     * @param eventType the event type
     * @return true if this state can apply the event
     */
    boolean canApply(String eventType);

    /**
     * Check if this state exists (has been created)
     *
     * @return true if the aggregate exists
     */
    default boolean exists() {
        return getVersion() > 0;
    }

    /**
     * Create an empty/initial state for the given aggregate
     *
     * @param aggregateId the aggregate identifier
     * @return empty state
     */
    AggregateState createEmpty(String aggregateId);
}
