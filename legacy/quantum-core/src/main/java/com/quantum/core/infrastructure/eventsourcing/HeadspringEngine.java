package com.quantum.core.infrastructure.eventsourcing;

import com.quantum.core.application.command.StreamCommand;
import com.quantum.core.application.event.DomainEvent;
import com.quantum.core.application.state.AggregateState;
import com.quantum.core.domain.port.eventsourcing.CommandExecutor;
import com.quantum.core.domain.port.eventsourcing.EventHandler;
import com.quantum.core.domain.port.eventsourcing.EventStore;
import com.quantum.core.domain.port.eventsourcing.Headspring;
import com.quantum.core.domain.port.messaging.MessageBus;
import java.util.List;
import java.util.Optional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * Main Event Sourcing engine implementation Coordinates command execution, event persistence, and
 * state management Based on the architecture from gangnamunni blog post
 */
@Component
public class HeadspringEngine implements Headspring {

    private static final Logger logger = LoggerFactory.getLogger(HeadspringEngine.class);

    private final EventStore eventStore;
    private final MessageBus messageBus;

    public HeadspringEngine(EventStore eventStore, MessageBus messageBus) {
        this.eventStore = eventStore;
        this.messageBus = messageBus;
    }

    @Override
    @Transactional
    public <T extends AggregateState> T executeCommand(
            StreamCommand command, CommandExecutor<T> executor) {
        CommandResult<T> result = executeCommandWithResult(command, executor);
        return result.getNewState();
    }

    @Override
    @Transactional
    public <T extends AggregateState> CommandResult<T> executeCommandWithResult(
            StreamCommand command, CommandExecutor<T> executor) {
        logger.debug(
                "Executing command: {} for stream: {}",
                command.getClass().getSimpleName(),
                command.getStreamId());

        try {
            // Validate command
            command.validate();

            // Load current state
            T currentState = loadCurrentState(command.getStreamId(), executor);

            // Validate command against current state
            executor.validate(command, currentState);

            // Execute command and get events
            List<DomainEvent> events = executor.execute(command, currentState);

            if (events == null || events.isEmpty()) {
                logger.debug(
                        "No events generated for command: {} on stream: {}",
                        command.getClass().getSimpleName(),
                        command.getStreamId());
                return new CommandResult<>(List.of(), currentState, currentState);
            }

            // Get expected version from current state or stream
            int expectedVersion = getExpectedVersion(command.getStreamId());

            // Persist events
            eventStore.appendEvents(command.getStreamId(), expectedVersion, events);

            // Apply events to get new state
            T newState = executor.applyEvents(currentState, events);

            // Publish events
            messageBus.publishAll(events);

            logger.info(
                    "Successfully executed command: {} for stream: {} generating {} events",
                    command.getClass().getSimpleName(),
                    command.getStreamId(),
                    events.size());

            return new CommandResult<>(events, newState, currentState);

        } catch (Exception e) {
            logger.error(
                    "Failed to execute command: {} for stream: {}",
                    command.getClass().getSimpleName(),
                    command.getStreamId(),
                    e);
            throw new CommandExecutionException(
                    String.format(
                            "Failed to execute command %s for stream %s",
                            command.getClass().getSimpleName(), command.getStreamId()),
                    e);
        }
    }

    @Override
    public <T extends AggregateState> Optional<T> loadAggregate(
            String streamId, CommandExecutor<T> executor) {
        logger.debug("Loading aggregate for stream: {}", streamId);

        try {
            if (!eventStore.streamExists(streamId)) {
                return Optional.empty();
            }

            List<DomainEvent> events = eventStore.readStream(streamId);
            if (events.isEmpty()) {
                return Optional.empty();
            }

            T initialState = executor.getInitialState(streamId);
            T currentState = executor.applyEvents(initialState, events);

            return Optional.of(currentState);

        } catch (Exception e) {
            logger.error("Failed to load aggregate for stream: {}", streamId, e);
            throw new AggregateLoadException(
                    String.format("Failed to load aggregate for stream %s", streamId), e);
        }
    }

    @Override
    public <T extends AggregateState> Optional<T> loadAggregateToVersion(
            String streamId, int version, CommandExecutor<T> executor) {
        logger.debug("Loading aggregate for stream: {} to version: {}", streamId, version);

        try {
            if (!eventStore.streamExists(streamId)) {
                return Optional.empty();
            }

            List<DomainEvent> events = eventStore.readStreamToVersion(streamId, version);
            if (events.isEmpty()) {
                return Optional.empty();
            }

            T initialState = executor.getInitialState(streamId);
            T currentState = executor.applyEvents(initialState, events);

            return Optional.of(currentState);

        } catch (Exception e) {
            logger.error(
                    "Failed to load aggregate for stream: {} to version: {}", streamId, version, e);
            throw new AggregateLoadException(
                    String.format(
                            "Failed to load aggregate for stream %s to version %d",
                            streamId, version),
                    e);
        }
    }

    @Override
    public <T extends AggregateState> Optional<T> rehydrate(
            String streamId, EventHandler<T> eventHandler, Class<T> stateClass) {
        logger.debug("Rehydrating state for stream: {}", streamId);

        try {
            if (!eventStore.streamExists(streamId)) {
                return Optional.empty();
            }

            List<DomainEvent> events = eventStore.readStream(streamId);
            if (events.isEmpty()) {
                return Optional.empty();
            }

            T initialState = eventHandler.getInitialState(streamId);
            T currentState = eventHandler.applyAll(initialState, events);

            return Optional.of(currentState);

        } catch (Exception e) {
            logger.error("Failed to rehydrate state for stream: {}", streamId, e);
            throw new AggregateLoadException(
                    String.format("Failed to rehydrate state for stream %s", streamId), e);
        }
    }

    @Override
    public <T extends AggregateState> Optional<T> rehydrateToVersion(
            String streamId, int toVersion, EventHandler<T> eventHandler, Class<T> stateClass) {
        logger.debug("Rehydrating state for stream: {} to version: {}", streamId, toVersion);

        try {
            if (!eventStore.streamExists(streamId)) {
                return Optional.empty();
            }

            List<DomainEvent> events = eventStore.readStreamToVersion(streamId, toVersion);
            if (events.isEmpty()) {
                return Optional.empty();
            }

            T initialState = eventHandler.getInitialState(streamId);
            T currentState = eventHandler.applyAll(initialState, events);

            return Optional.of(currentState);

        } catch (Exception e) {
            logger.error(
                    "Failed to rehydrate state for stream: {} to version: {}",
                    streamId,
                    toVersion,
                    e);
            throw new AggregateLoadException(
                    String.format(
                            "Failed to rehydrate state for stream %s to version %d",
                            streamId, toVersion),
                    e);
        }
    }

    @Override
    public List<DomainEvent> getEvents(String streamId) {
        logger.debug("Getting all events for stream: {}", streamId);
        return eventStore.readStream(streamId);
    }

    @Override
    public List<DomainEvent> getEvents(String streamId, int fromVersion) {
        logger.debug("Getting events for stream: {} from version: {}", streamId, fromVersion);
        return eventStore.readStream(streamId, fromVersion);
    }

    @Override
    public List<DomainEvent> getEventsByType(String eventType) {
        logger.debug("Getting all events of type: {}", eventType);
        return eventStore.getEventsByType(eventType);
    }

    @Override
    public boolean streamExists(String streamId) {
        return eventStore.streamExists(streamId);
    }

    @Override
    public Optional<Integer> getStreamVersion(String streamId) {
        return eventStore.getStreamVersion(streamId);
    }

    @Override
    public void subscribe(String streamPattern, EventHandler<?> eventHandler) {
        logger.info("Subscribing handler to stream pattern: {}", streamPattern);
        // Convert EventHandler to EventStore's EventHandler interface
        EventStore.EventHandler storeHandler =
                event -> {
                    // This is a simple bridge - in a real implementation, you might want more
                    // sophisticated handling
                    String eventType = event.getClass().getSimpleName();
                    if (eventHandler.canHandle(eventType)) {
                        // Apply the event (this would typically be used for projections or read
                        // models)
                        logger.debug(
                                "Processing event {} with handler {}",
                                eventType,
                                eventHandler.getClass().getSimpleName());
                    }
                };
        eventStore.subscribe(streamPattern, storeHandler);
    }

    @Override
    public EventStore getEventStore() {
        return eventStore;
    }

    private <T extends AggregateState> T loadCurrentState(
            String streamId, CommandExecutor<T> executor) {
        Optional<T> state = loadAggregate(streamId, executor);
        return state.orElse(executor.getInitialState(streamId));
    }

    private int getExpectedVersion(String streamId) {
        return eventStore.getStreamVersion(streamId).orElse(-1);
    }

    /** Exception thrown when command execution fails */
    public static class CommandExecutionException extends RuntimeException {
        public CommandExecutionException(String message) {
            super(message);
        }

        public CommandExecutionException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    /** Exception thrown when aggregate loading fails */
    public static class AggregateLoadException extends RuntimeException {
        public AggregateLoadException(String message) {
            super(message);
        }

        public AggregateLoadException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
