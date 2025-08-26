package com.quantum.trading.platform.query.view;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

/**
 * 키움증권 계좌 조회용 View Entity
 * 
 * CQRS Query Side - 키움증권 계좌 정보를 효율적으로 조회하기 위한 비정규화 테이블
 * Event Handler에서 이벤트를 구독하여 업데이트됨
 */
@Entity
@Table(name = "kiwoom_account_view", indexes = {
    @Index(name = "idx_kiwoom_user_id", columnList = "user_id"),
    @Index(name = "idx_kiwoom_account_id", columnList = "kiwoom_account_id", unique = true),
    @Index(name = "idx_kiwoom_assigned_at", columnList = "assigned_at")
})
@Getter
@Setter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class KiwoomAccountView {

    @Id
    @Column(name = "user_id", length = 100)
    private String userId;

    @Column(name = "kiwoom_account_id", length = 8, nullable = false, unique = true)
    private String kiwoomAccountId;

    @Column(name = "encrypted_client_id", columnDefinition = "TEXT")
    private String encryptedClientId;

    @Column(name = "encrypted_client_secret", columnDefinition = "TEXT")
    private String encryptedClientSecret;

    @Column(name = "encryption_salt", length = 255)
    private String encryptionSalt;

    @Column(name = "assigned_at", nullable = false)
    private Instant assignedAt;

    @Column(name = "credentials_updated_at")
    private Instant credentialsUpdatedAt;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @PrePersist
    protected void onCreate() {
        Instant now = Instant.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = Instant.now();
    }

    // Factory methods
    public static KiwoomAccountView create(
            String userId,
            String kiwoomAccountId,
            String encryptedClientId,
            String encryptedClientSecret,
            String encryptionSalt,
            Instant assignedAt
    ) {
        KiwoomAccountView view = new KiwoomAccountView();
        view.userId = userId;
        view.kiwoomAccountId = kiwoomAccountId;
        view.encryptedClientId = encryptedClientId;
        view.encryptedClientSecret = encryptedClientSecret;
        view.encryptionSalt = encryptionSalt;
        view.assignedAt = assignedAt;
        view.credentialsUpdatedAt = assignedAt;
        view.isActive = true;
        return view;
    }

    // Business methods
    public void updateCredentials(String encryptedClientId, String encryptedClientSecret, String encryptionSalt) {
        this.encryptedClientId = encryptedClientId;
        this.encryptedClientSecret = encryptedClientSecret;
        this.encryptionSalt = encryptionSalt;
        this.credentialsUpdatedAt = Instant.now();
    }

    public void revoke() {
        this.isActive = false;
    }

    public boolean hasValidCredentials() {
        return this.encryptedClientId != null && 
               this.encryptedClientSecret != null && 
               this.encryptionSalt != null &&
               this.isActive;
    }
}