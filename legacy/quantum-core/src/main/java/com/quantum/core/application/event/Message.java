package com.quantum.core.application.event;

import java.time.LocalDateTime;

/** Base interface for all messages (commands and events) in the system */
public interface Message {
    /** Unique identifier for this message */
    String getId();

    /** Correlation identifier for tracking related messages */
    String getCorrelationId();

    /** Timestamp when this message was created */
    LocalDateTime getTimestamp();

    /** Type identifier for this message */
    String getType();

    /** The actual data payload of this message */
    Object getData();

    /** Version of the message schema */
    default int getVersion() {
        return 1;
    }
}
