package com.quantum.common

import java.time.LocalDateTime

/**
 * 도메인 이벤트 베이스 인터페이스
 */
interface DomainEvent {
    val eventId: String
    val occurredAt: LocalDateTime
    val aggregateId: String
    val eventType: String
}