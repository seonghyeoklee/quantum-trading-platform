package com.quantum.core.infrastructure.common;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.Comment;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

/**
 * 공통 시간 필드를 관리하는 기본 엔티티
 *
 * <p>모든 엔티티의 생성, 수정, 삭제 시간을 자동으로 관리합니다. JPA Auditing을 사용하여 시간 필드가 자동으로 설정됩니다.
 */
@Getter
@Setter(lombok.AccessLevel.PROTECTED)
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class BaseTimeEntity {

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    @Comment("생성일시")
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    @Comment("수정일시")
    private LocalDateTime updatedAt;

    @Column(name = "deleted_at")
    @Comment("삭제일시")
    private LocalDateTime deletedAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
        if (updatedAt == null) {
            updatedAt = LocalDateTime.now();
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    /** 소프트 삭제 처리 */
    public void delete() {
        this.deletedAt = LocalDateTime.now();
    }

    /** 삭제 여부 확인 */
    public boolean isDeleted() {
        return deletedAt != null;
    }

    /** 삭제 취소 (소프트 삭제 복구) */
    public void restore() {
        this.deletedAt = null;
    }
}
