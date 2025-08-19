package com.quantum.core.domain.port.eventsourcing;

import com.quantum.core.application.event.DomainEvent;
import com.quantum.core.application.state.AggregateState;
import java.util.List;

/** Interface for rehydrating aggregate state from events */
public interface StateRehydrator {

    /**
     * Rehydrate state from a stream of events
     *
     * @param aggregateId the aggregate identifier
     * @param aggregateType the aggregate type
     * @param events the events to apply
     * @return the rehydrated state
     */
    AggregateState rehydrate(String aggregateId, String aggregateType, List<DomainEvent> events);

    /**
     * Rehydrate state from events up to a specific version
     *
     * @param aggregateId the aggregate identifier
     * @param aggregateType the aggregate type
     * @param events the events to apply
     * @param toVersion the target version (inclusive)
     * @return the rehydrated state
     */
    AggregateState rehydrateToVersion(
            String aggregateId, String aggregateType, List<DomainEvent> events, int toVersion);

    /**
     * Register a state factory for a specific aggregate type
     *
     * @param aggregateType the aggregate type
     * @param stateFactory factory to create empty states
     */
    void registerStateFactory(String aggregateType, StateFactory stateFactory);

    /**
     * Check if a state factory is registered for the given aggregate type
     *
     * @param aggregateType the aggregate type
     * @return true if a factory is registered
     */
    boolean hasStateFactory(String aggregateType);

    /** Factory interface for creating empty aggregate states */
    @FunctionalInterface
    interface StateFactory {
        AggregateState createEmpty(String aggregateId);
    }
}
