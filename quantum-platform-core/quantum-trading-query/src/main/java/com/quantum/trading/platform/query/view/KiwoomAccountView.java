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

    @Column(name = "client_id", length = 255)
    private String clientId;

    @Column(name = "client_secret", length = 255)
    private String clientSecret;

    // === Sandbox 모드 키 관리 ===
    @Column(name = "sandbox_app_key", length = 255)
    private String sandboxAppKey;

    @Column(name = "sandbox_app_secret", length = 255)
    private String sandboxAppSecret;

    @Column(name = "sandbox_access_token", columnDefinition = "TEXT")
    private String sandboxAccessToken;

    @Column(name = "sandbox_token_expires_at")
    private Instant sandboxTokenExpiresAt;

    // === Real 모드 키 관리 ===
    @Column(name = "real_app_key", length = 255)
    private String realAppKey;

    @Column(name = "real_app_secret", length = 255)
    private String realAppSecret;

    @Column(name = "real_access_token", columnDefinition = "TEXT")
    private String realAccessToken;

    @Column(name = "real_token_expires_at")
    private Instant realTokenExpiresAt;

    // === 토큰 관리 메타데이터 ===
    @Column(name = "token_version", nullable = false)
    private Integer tokenVersion = 1;

    @Column(name = "last_token_refresh_at")
    private Instant lastTokenRefreshAt;

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
            String clientId,
            String clientSecret,
            Instant assignedAt
    ) {
        KiwoomAccountView view = new KiwoomAccountView();
        view.userId = userId;
        view.kiwoomAccountId = kiwoomAccountId;
        view.clientId = clientId;
        view.clientSecret = clientSecret;
        view.assignedAt = assignedAt;
        view.credentialsUpdatedAt = assignedAt;
        view.isActive = true;
        return view;
    }

    // Business methods
    public void updateCredentials(String clientId, String clientSecret) {
        this.clientId = clientId;
        this.clientSecret = clientSecret;
        this.credentialsUpdatedAt = Instant.now();
    }

    public void revoke() {
        this.isActive = false;
    }

    public boolean hasValidCredentials() {
        return this.clientId != null && 
               this.clientSecret != null && 
               this.isActive;
    }

    // === Sandbox 모드 키 관리 메서드 ===
    public void updateSandboxApiKeys(String sandboxAppKey, String sandboxAppSecret) {
        this.sandboxAppKey = sandboxAppKey;
        this.sandboxAppSecret = sandboxAppSecret;
        this.credentialsUpdatedAt = Instant.now();
    }

    public void updateSandboxAccessToken(String sandboxAccessToken, Instant expiresAt) {
        this.sandboxAccessToken = sandboxAccessToken;
        this.sandboxTokenExpiresAt = expiresAt;
        this.lastTokenRefreshAt = Instant.now();
    }

    public boolean hasSandboxApiKeys() {
        return this.sandboxAppKey != null && 
               this.sandboxAppSecret != null;
    }

    public boolean isSandboxTokenValid() {
        return this.sandboxAccessToken != null &&
               this.sandboxTokenExpiresAt != null &&
               this.sandboxTokenExpiresAt.isAfter(Instant.now());
    }

    // === Real 모드 키 관리 메서드 ===
    public void updateRealApiKeys(String realAppKey, String realAppSecret) {
        this.realAppKey = realAppKey;
        this.realAppSecret = realAppSecret;
        this.credentialsUpdatedAt = Instant.now();
    }

    public void updateRealAccessToken(String realAccessToken, Instant expiresAt) {
        this.realAccessToken = realAccessToken;
        this.realTokenExpiresAt = expiresAt;
        this.lastTokenRefreshAt = Instant.now();
    }

    public boolean hasRealApiKeys() {
        return this.realAppKey != null && 
               this.realAppSecret != null;
    }

    public boolean isRealTokenValid() {
        return this.realAccessToken != null &&
               this.realTokenExpiresAt != null &&
               this.realTokenExpiresAt.isAfter(Instant.now());
    }

    // === 모드별 토큰 유효성 검사 ===
    public boolean isTokenValid(boolean isRealMode) {
        return isRealMode ? isRealTokenValid() : isSandboxTokenValid();
    }

    public boolean hasApiKeys(boolean isRealMode) {
        return isRealMode ? hasRealApiKeys() : hasSandboxApiKeys();
    }

    public Instant getTokenExpiresAt(boolean isRealMode) {
        return isRealMode ? realTokenExpiresAt : sandboxTokenExpiresAt;
    }

    // === 토큰 버전 관리 ===
    public void incrementTokenVersion() {
        this.tokenVersion++;
    }
}