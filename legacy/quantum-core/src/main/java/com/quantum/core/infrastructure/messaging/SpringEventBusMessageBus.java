package com.quantum.core.infrastructure.messaging;

import com.quantum.core.application.command.StreamCommand;
import com.quantum.core.application.event.DomainEvent;
import com.quantum.core.domain.port.messaging.MessageBus;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/** Spring Events-based implementation of MessageBus */
@Component
public class SpringEventBusMessageBus implements MessageBus {

    private static final Logger logger = LoggerFactory.getLogger(SpringEventBusMessageBus.class);

    private final ApplicationEventPublisher eventPublisher;
    private final Map<String, AtomicLong> eventCounters;
    private final Map<String, List<MessageBus.EventHandler>> eventSubscribers;
    private final Map<String, MessageBus.CommandHandler> commandHandlers;
    private final AtomicBoolean started;

    public SpringEventBusMessageBus(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
        this.eventCounters = new ConcurrentHashMap<>();
        this.eventSubscribers = new ConcurrentHashMap<>();
        this.commandHandlers = new ConcurrentHashMap<>();
        this.started = new AtomicBoolean(false);
    }

    @Override
    public void publish(DomainEvent event) {
        if (event == null) {
            logger.warn("Attempted to publish null event");
            return;
        }

        if (!started.get()) {
            logger.warn(
                    "Message bus is not started, event will not be published: {}", event.getType());
            return;
        }

        try {
            logger.debug(
                    "Publishing domain event: {} for aggregate: {}",
                    event.getType(),
                    event.getAggregateId());

            // Increment counter for event type
            eventCounters
                    .computeIfAbsent(event.getType(), k -> new AtomicLong(0))
                    .incrementAndGet();

            // Notify direct subscribers
            notifySubscribers(event);

            // Publish using Spring's event mechanism for async processing
            eventPublisher.publishEvent(new DomainEventWrapper(event));

            logger.trace("Successfully published event: {}", event.getType());

        } catch (Exception e) {
            logger.error(
                    "Failed to publish event: {} for aggregate: {}",
                    event.getType(),
                    event.getAggregateId(),
                    e);
            throw new MessagePublishingException("Failed to publish event", e);
        }
    }

    @Override
    public void publishAll(Iterable<DomainEvent> events) {
        if (events == null) {
            logger.warn("Attempted to publish null events collection");
            return;
        }

        int publishedCount = 0;
        for (DomainEvent event : events) {
            try {
                publish(event);
                publishedCount++;
            } catch (Exception e) {
                logger.error(
                        "Failed to publish event in batch: {} at position: {}",
                        event.getType(),
                        publishedCount,
                        e);
                // Continue with other events instead of failing completely
            }
        }

        logger.debug("Published {} events in batch", publishedCount);
    }

    @Override
    public void send(StreamCommand command) {
        if (command == null) {
            logger.warn("Attempted to send null command");
            return;
        }

        if (!started.get()) {
            logger.warn(
                    "Message bus is not started, command will not be sent: {}",
                    command.getClass().getSimpleName());
            return;
        }

        try {
            String commandType = command.getClass().getSimpleName();
            MessageBus.CommandHandler handler = commandHandlers.get(commandType);

            if (handler != null && handler.canHandle(commandType)) {
                logger.debug(
                        "Sending command: {} for stream: {}", commandType, command.getStreamId());
                handler.handle(command);
                logger.trace("Successfully sent command: {}", commandType);
            } else {
                logger.warn("No handler registered for command type: {}", commandType);
                throw new MessagePublishingException(
                        "No handler registered for command type: " + commandType);
            }

        } catch (Exception e) {
            logger.error(
                    "Failed to send command: {} for stream: {}",
                    command.getClass().getSimpleName(),
                    command.getStreamId(),
                    e);
            throw new MessagePublishingException("Failed to send command", e);
        }
    }

    @Override
    public void subscribe(String eventType, MessageBus.EventHandler handler) {
        if (eventType == null || handler == null) {
            logger.warn("Cannot subscribe with null eventType or handler");
            return;
        }

        eventSubscribers.computeIfAbsent(eventType, k -> new CopyOnWriteArrayList<>()).add(handler);
        logger.info("Subscribed handler to event type: {}", eventType);
    }

    @Override
    public void subscribeToPattern(String eventPattern, MessageBus.EventHandler handler) {
        if (eventPattern == null || handler == null) {
            logger.warn("Cannot subscribe with null eventPattern or handler");
            return;
        }

        // For simplicity, treat pattern subscription same as type subscription
        // In a real implementation, you might want pattern matching logic
        eventSubscribers
                .computeIfAbsent(eventPattern, k -> new CopyOnWriteArrayList<>())
                .add(handler);
        logger.info("Subscribed handler to event pattern: {}", eventPattern);
    }

    @Override
    public void unsubscribe(String eventType, MessageBus.EventHandler handler) {
        if (eventType == null || handler == null) {
            logger.warn("Cannot unsubscribe with null eventType or handler");
            return;
        }

        List<MessageBus.EventHandler> handlers = eventSubscribers.get(eventType);
        if (handlers != null) {
            handlers.remove(handler);
            if (handlers.isEmpty()) {
                eventSubscribers.remove(eventType);
            }
            logger.info("Unsubscribed handler from event type: {}", eventType);
        }
    }

    @Override
    public void registerCommandHandler(String commandType, MessageBus.CommandHandler handler) {
        if (commandType == null || handler == null) {
            logger.warn("Cannot register handler with null commandType or handler");
            return;
        }

        commandHandlers.put(commandType, handler);
        logger.info("Registered command handler for type: {}", commandType);
    }

    @Override
    public void start() {
        if (started.compareAndSet(false, true)) {
            logger.info("Message bus started");
        } else {
            logger.warn("Message bus is already started");
        }
    }

    @Override
    public void stop() {
        if (started.compareAndSet(true, false)) {
            eventSubscribers.clear();
            commandHandlers.clear();
            logger.info("Message bus stopped and cleared all handlers");
        } else {
            logger.warn("Message bus is already stopped");
        }
    }

    /** Notify direct subscribers of an event */
    private void notifySubscribers(DomainEvent event) {
        String eventType = event.getType();
        List<MessageBus.EventHandler> handlers = eventSubscribers.get(eventType);

        if (handlers != null && !handlers.isEmpty()) {
            for (MessageBus.EventHandler handler : handlers) {
                try {
                    if (handler.canHandle(eventType)) {
                        handler.handle(event);
                    }
                } catch (Exception e) {
                    logger.error(
                            "Error in event handler for type: {}, event: {}", eventType, event, e);
                }
            }
        }
    }

    /** Get event count statistics */
    public Map<String, Long> getEventCounts() {
        return eventCounters.entrySet().stream()
                .collect(
                        java.util.stream.Collectors.toMap(
                                Map.Entry::getKey, entry -> entry.getValue().get()));
    }

    /** Reset event count statistics */
    public void resetEventCounts() {
        eventCounters.clear();
        logger.info("Event count statistics reset");
    }

    /** Check if message bus is started */
    public boolean isStarted() {
        return started.get();
    }

    /** Spring Event wrapper for domain events */
    public static class DomainEventWrapper {
        private final DomainEvent event;

        public DomainEventWrapper(DomainEvent event) {
            this.event = event;
        }

        public DomainEvent getEvent() {
            return event;
        }
    }

    /** Async event listener for domain events */
    @EventListener
    @Async
    public void handleDomainEventAsync(DomainEventWrapper eventWrapper) {
        DomainEvent event = eventWrapper.getEvent();

        logger.debug(
                "Handling domain event asynchronously: {} for aggregate: {}",
                event.getType(),
                event.getAggregateId());

        // This is where additional async domain event processing could happen
        // For example: updating read models, sending notifications, etc.
        logger.trace("Domain event processed asynchronously: {}", event.getType());
    }

    /** Exception thrown when event publishing or command sending fails */
    public static class MessagePublishingException extends RuntimeException {
        public MessagePublishingException(String message) {
            super(message);
        }

        public MessagePublishingException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
