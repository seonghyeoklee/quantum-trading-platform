package com.quantum.core.application.command;

import com.quantum.core.application.event.Message;

/** Interface for commands that target specific aggregate streams */
public interface StreamCommand extends Message {
    /** The stream identifier (usually aggregate ID) */
    String getStreamId();

    /** Expected version for optimistic concurrency control */
    int getExpectedVersion();

    /** Validate the command before execution */
    default void validate() {
        // Default implementation - can be overridden
    }
}
