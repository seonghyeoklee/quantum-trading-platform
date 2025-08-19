package com.quantum.core.infrastructure.persistence;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

/** JPA Repository for EventStoreEntity */
@Repository
public interface EventStoreRepository extends JpaRepository<EventStoreEntity, Long> {

    /** Find all events for a stream ordered by version */
    List<EventStoreEntity> findByStreamIdOrderByVersionAsc(String streamId);

    /** Find events for a stream from a specific version */
    @Query(
            "SELECT e FROM EventStoreEntity e WHERE e.streamId = :streamId AND e.version >= :fromVersion ORDER BY e.version ASC")
    List<EventStoreEntity> findByStreamIdFromVersion(
            @Param("streamId") String streamId, @Param("fromVersion") int fromVersion);

    /** Find events for a stream up to a specific version */
    @Query(
            "SELECT e FROM EventStoreEntity e WHERE e.streamId = :streamId AND e.version <= :toVersion ORDER BY e.version ASC")
    List<EventStoreEntity> findByStreamIdToVersion(
            @Param("streamId") String streamId, @Param("toVersion") int toVersion);

    /** Get the current version of a stream */
    @Query("SELECT MAX(e.version) FROM EventStoreEntity e WHERE e.streamId = :streamId")
    Optional<Integer> findMaxVersionByStreamId(@Param("streamId") String streamId);

    /** Check if a stream exists */
    boolean existsByStreamId(String streamId);

    /** Find all events of a specific type */
    List<EventStoreEntity> findByEventTypeOrderByCreatedAtAsc(String eventType);

    /** Find events by aggregate type */
    List<EventStoreEntity> findByAggregateTypeOrderByCreatedAtAsc(String aggregateType);

    /** Find events by correlation ID */
    List<EventStoreEntity> findByCorrelationIdOrderByCreatedAtAsc(String correlationId);

    /** Check for concurrent modification */
    @Query(
            "SELECT COUNT(e) FROM EventStoreEntity e WHERE e.streamId = :streamId AND e.version > :expectedVersion")
    long countByStreamIdAndVersionGreaterThan(
            @Param("streamId") String streamId, @Param("expectedVersion") int expectedVersion);
}
