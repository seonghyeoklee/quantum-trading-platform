package com.quantum.core.application.command;

import com.quantum.core.application.event.AbstractMessage;

/** Abstract base implementation for stream commands */
public abstract class AbstractStreamCommand extends AbstractMessage implements StreamCommand {

    private final String streamId;
    private final int expectedVersion;

    protected AbstractStreamCommand(String streamId, int expectedVersion, String correlationId) {
        super(correlationId);
        this.streamId = streamId;
        this.expectedVersion = expectedVersion;
    }

    protected AbstractStreamCommand(String streamId, int expectedVersion) {
        this(streamId, expectedVersion, null);
    }

    protected AbstractStreamCommand(String streamId) {
        this(streamId, -1, null); // -1 means any version
    }

    @Override
    public String getStreamId() {
        return streamId;
    }

    @Override
    public int getExpectedVersion() {
        return expectedVersion;
    }

    @Override
    public String toString() {
        return String.format(
                "%s{id='%s', streamId='%s', expectedVersion=%d, timestamp=%s}",
                getType(), getId(), streamId, expectedVersion, getTimestamp());
    }
}
