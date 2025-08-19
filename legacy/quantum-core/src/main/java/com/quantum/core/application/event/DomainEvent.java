package com.quantum.core.application.event;

/** Base interface for domain events */
public interface DomainEvent extends Message {
    /** The aggregate ID that generated this event */
    String getAggregateId();

    /** The aggregate type that generated this event */
    String getAggregateType();

    /** The version of the aggregate when this event was generated */
    int getAggregateVersion();

    /** User or system that triggered this event */
    String getTriggeredBy();
}
