package com.quantum.common

import jakarta.persistence.*
import org.springframework.data.annotation.CreatedDate
import org.springframework.data.annotation.LastModifiedDate
import org.springframework.data.jpa.domain.support.AuditingEntityListener
import java.time.LocalDateTime

@MappedSuperclass
@EntityListeners(AuditingEntityListener::class)
abstract class BaseEntity {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0L
    
    @CreatedDate
    @Column(nullable = false, updatable = false)
    lateinit var createdAt: LocalDateTime
        private set
    
    @LastModifiedDate
    @Column(nullable = false)
    lateinit var updatedAt: LocalDateTime
        private set
    
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other == null || this::class != other::class) return false
        other as BaseEntity
        return id == other.id
    }
    
    override fun hashCode(): Int = id.hashCode()
}