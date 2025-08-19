package com.quantum.core.domain.port.messaging;

import com.quantum.core.application.command.StreamCommand;
import com.quantum.core.application.event.DomainEvent;

/** Message Bus interface for publishing events and sending commands */
public interface MessageBus {

    /**
     * Publish a domain event asynchronously
     *
     * @param event the event to publish
     */
    void publish(DomainEvent event);

    /**
     * Publish multiple domain events asynchronously
     *
     * @param events the events to publish
     */
    void publishAll(Iterable<DomainEvent> events);

    /**
     * Send a command for processing
     *
     * @param command the command to send
     */
    void send(StreamCommand command);

    /**
     * Subscribe to events of a specific type
     *
     * @param eventType the event type to subscribe to
     * @param handler the event handler
     */
    void subscribe(String eventType, MessageBus.EventHandler handler);

    /**
     * Subscribe to all events matching a pattern
     *
     * @param eventPattern pattern to match (e.g., "*.OrderEvent", "Stock.*")
     * @param handler the event handler
     */
    void subscribeToPattern(String eventPattern, MessageBus.EventHandler handler);

    /**
     * Unsubscribe from events
     *
     * @param eventType the event type to unsubscribe from
     * @param handler the event handler to remove
     */
    void unsubscribe(String eventType, MessageBus.EventHandler handler);

    /**
     * Register a command handler
     *
     * @param commandType the command type
     * @param handler the command handler
     */
    void registerCommandHandler(String commandType, MessageBus.CommandHandler handler);

    /** Start the message bus */
    void start();

    /** Stop the message bus */
    void stop();

    /** Command handler interface for processing commands */
    interface CommandHandler {
        /**
         * Handle a command
         *
         * @param command the command to handle
         */
        void handle(StreamCommand command);

        /**
         * Check if this handler can handle the given command type
         *
         * @param commandType the command type to check
         * @return true if this handler can handle the command type
         */
        boolean canHandle(String commandType);
    }

    /** Event handler interface for processing events */
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
        boolean canHandle(String eventType);
    }
}
