package com.quantum.core.infrastructure.persistence;

import com.quantum.core.infrastructure.common.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** JPA Entity for storing events in the event store */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
@Table(
        name = "tb_event_store",
        indexes = {
            @Index(name = "idx_stream_id", columnList = "streamId"),
            @Index(name = "idx_stream_id_version", columnList = "streamId, version"),
            @Index(name = "idx_event_type", columnList = "eventType"),
            @Index(name = "idx_aggregate_type", columnList = "aggregateType"),
            @Index(name = "idx_created_at", columnList = "createdAt")
        })
public class EventStoreEntity extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String eventId;

    @Column(nullable = false, length = 100)
    private String streamId;

    @Column(nullable = false)
    private Integer version;

    @Column(nullable = false, length = 100)
    private String eventType;

    @Column(nullable = false, length = 50)
    private String aggregateType;

    @Column(nullable = false, length = 100)
    private String aggregateId;

    @Column(nullable = false, length = 100)
    private String correlationId;

    @Column(nullable = false, length = 100)
    private String triggeredBy;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String eventData;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String metadata;

    public EventStoreEntity(
            String eventId,
            String streamId,
            Integer version,
            String eventType,
            String aggregateType,
            String aggregateId,
            String correlationId,
            String triggeredBy,
            String eventData,
            String metadata) {
        this.eventId = eventId;
        this.streamId = streamId;
        this.version = version;
        this.eventType = eventType;
        this.aggregateType = aggregateType;
        this.aggregateId = aggregateId;
        this.correlationId = correlationId;
        this.triggeredBy = triggeredBy;
        this.eventData = eventData;
        this.metadata = metadata;
    }

    @Override
    public String toString() {
        return String.format(
                "EventStoreEntity{id=%d, eventId='%s', streamId='%s', version=%d, eventType='%s', aggregateType='%s'}",
                id, eventId, streamId, version, eventType, aggregateType);
    }
}
