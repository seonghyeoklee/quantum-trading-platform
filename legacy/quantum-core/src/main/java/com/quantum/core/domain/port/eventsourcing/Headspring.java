package com.quantum.core.domain.port.eventsourcing;

import com.quantum.core.application.command.StreamCommand;
import com.quantum.core.application.event.DomainEvent;
import com.quantum.core.application.state.AggregateState;
import java.util.List;
import java.util.Optional;

/** Core Event Sourcing engine interface Provides domain-agnostic event sourcing capabilities */
public interface Headspring {

    /**
     * Execute a command and return the new aggregate state
     *
     * @param command the command to execute
     * @param executor the command executor
     * @param <T> the aggregate state type
     * @return the new aggregate state after applying generated events
     */
    <T extends AggregateState> T executeCommand(StreamCommand command, CommandExecutor<T> executor);

    /**
     * Execute a command and return both events and new state
     *
     * @param command the command to execute
     * @param executor the command executor
     * @param <T> the aggregate state type
     * @return execution result containing events and new state
     */
    <T extends AggregateState> CommandResult<T> executeCommandWithResult(
            StreamCommand command, CommandExecutor<T> executor);

    /**
     * Load current aggregate state from event stream
     *
     * @param streamId the stream identifier
     * @param executor the command executor (provides initial state and event handling)
     * @param <T> the aggregate state type
     * @return the current aggregate state, or empty if stream doesn't exist
     */
    <T extends AggregateState> Optional<T> loadAggregate(
            String streamId, CommandExecutor<T> executor);

    /**
     * Load aggregate state up to a specific version
     *
     * @param streamId the stream identifier
     * @param version the target version
     * @param executor the command executor
     * @param <T> the aggregate state type
     * @return the aggregate state at the specified version
     */
    <T extends AggregateState> Optional<T> loadAggregateToVersion(
            String streamId, int version, CommandExecutor<T> executor);

    /**
     * Rehydrate state from event stream using event handler
     *
     * @param streamId the stream identifier
     * @param eventHandler the event handler
     * @param stateClass the state class
     * @param <T> the aggregate state type
     * @return the rehydrated state, or empty if stream doesn't exist
     */
    <T extends AggregateState> Optional<T> rehydrate(
            String streamId, EventHandler<T> eventHandler, Class<T> stateClass);

    /**
     * Rehydrate state up to a specific version
     *
     * @param streamId the stream identifier
     * @param toVersion the target version
     * @param eventHandler the event handler
     * @param stateClass the state class
     * @param <T> the aggregate state type
     * @return the rehydrated state up to the specified version
     */
    <T extends AggregateState> Optional<T> rehydrateToVersion(
            String streamId, int toVersion, EventHandler<T> eventHandler, Class<T> stateClass);

    /**
     * Get all events for a stream
     *
     * @param streamId the stream identifier
     * @return list of events in chronological order
     */
    List<DomainEvent> getEvents(String streamId);

    /**
     * Get events starting from a specific version
     *
     * @param streamId the stream identifier
     * @param fromVersion the starting version (inclusive)
     * @return list of events from the specified version
     */
    List<DomainEvent> getEvents(String streamId, int fromVersion);

    /**
     * Get all events of a specific type across all streams
     *
     * @param eventType the event type
     * @return list of matching events
     */
    List<DomainEvent> getEventsByType(String eventType);

    /**
     * Check if a stream exists
     *
     * @param streamId the stream identifier
     * @return true if the stream exists
     */
    boolean streamExists(String streamId);

    /**
     * Get the current version of a stream
     *
     * @param streamId the stream identifier
     * @return the current version, or empty if stream doesn't exist
     */
    Optional<Integer> getStreamVersion(String streamId);

    /**
     * Subscribe to events matching a pattern
     *
     * @param streamPattern the stream pattern to match
     * @param eventHandler the event handler
     */
    void subscribe(String streamPattern, EventHandler<?> eventHandler);

    /**
     * Get access to the underlying event store
     *
     * @return the event store
     */
    EventStore getEventStore();

    /** Result of command execution */
    class CommandResult<T extends AggregateState> {
        private final List<DomainEvent> events;
        private final T newState;
        private final T previousState;

        public CommandResult(List<DomainEvent> events, T newState, T previousState) {
            this.events = events;
            this.newState = newState;
            this.previousState = previousState;
        }

        public List<DomainEvent> getEvents() {
            return events;
        }

        public T getNewState() {
            return newState;
        }

        public T getPreviousState() {
            return previousState;
        }

        public boolean hasEvents() {
            return events != null && !events.isEmpty();
        }

        public int getEventCount() {
            return events != null ? events.size() : 0;
        }
    }
}
