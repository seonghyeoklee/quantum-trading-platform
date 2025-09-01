package com.quantum.trading.platform.query.view;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.UserStatus;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.HashSet;
import java.util.Set;

/**
 * User 조회용 View Entity
 * 
 * Event Sourcing의 Read Model로 사용되며
 * 사용자 정보 조회 최적화를 위한 비정규화 테이블
 */
@Entity
@Table(name = "user_view", indexes = {
    @Index(name = "idx_user_view_username", columnList = "username"),
    @Index(name = "idx_user_view_email", columnList = "email"),
    @Index(name = "idx_user_view_status", columnList = "status"),
    @Index(name = "idx_user_view_created_at", columnList = "created_at")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserView {
    
    @Id
    @Column(name = "user_id", length = 50)
    private String userId;
    
    @Column(name = "username", unique = true, nullable = false, length = 50)
    private String username;
    
    @Column(name = "name", nullable = false, length = 100)
    private String name;
    
    @Column(name = "email", unique = true, nullable = false, length = 100)
    private String email;
    
    @Column(name = "phone", length = 20)
    private String phone;
    
    @Column(name = "password_hash", nullable = true, length = 255)
    private String passwordHash;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private UserStatus status;
    
    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(
        name = "user_roles", 
        joinColumns = @JoinColumn(name = "user_id"),
        indexes = @Index(name = "idx_user_roles_user_id", columnList = "user_id")
    )
    @Column(name = "role_name", length = 50)
    private Set<String> roles;
    
    @Column(name = "failed_login_attempts", nullable = false)
    @Builder.Default
    private Integer failedLoginAttempts = 0;
    
    @Column(name = "last_login_at")
    private Instant lastLoginAt;
    
    @Column(name = "last_failed_login_at")
    private Instant lastFailedLoginAt;
    
    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
    
    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;
    
    @Column(name = "registered_by", length = 50)
    private String registeredBy;
    
    @Column(name = "active_session_id", length = 100)
    private String activeSessionId;
    
    @Column(name = "session_start_time")
    private Instant sessionStartTime;
    
    // 2FA (Two-Factor Authentication) 관련 필드
    @Column(name = "two_factor_enabled", nullable = false)
    @Builder.Default
    private Boolean twoFactorEnabled = false;
    
    @Column(name = "totp_secret_key", length = 32)
    private String totpSecretKey;
    
    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(
        name = "user_backup_codes", 
        joinColumns = @JoinColumn(name = "user_id"),
        indexes = @Index(name = "idx_user_backup_codes_user_id", columnList = "user_id")
    )
    @Column(name = "backup_code_hash", length = 100)
    @Builder.Default
    private Set<String> backupCodeHashes = new HashSet<>();
    
    @Column(name = "two_factor_setup_at")
    private Instant twoFactorSetupAt;
    
    // Kiwoom Account Integration
    @Column(name = "kiwoom_account_id", length = 8)
    private String kiwoomAccountId;
    
    @Column(name = "kiwoom_account_assigned_at")
    private Instant kiwoomAccountAssignedAt;
    
    @Column(name = "kiwoom_credentials_updated_at")
    private Instant kiwoomCredentialsUpdatedAt;
    
    @Version
    private Long version;
    
    /**
     * 도메인 UserId로 변환
     */
    public UserId getUserIdValue() {
        return UserId.of(this.userId);
    }
    
    /**
     * 활성 세션 여부 확인
     */
    public boolean hasActiveSession() {
        return activeSessionId != null && !activeSessionId.trim().isEmpty();
    }
    
    /**
     * 로그인 가능 상태 확인
     */
    public boolean canLogin() {
        return status == UserStatus.ACTIVE && failedLoginAttempts < 5;
    }
    
    /**
     * 계정 잠금 상태 확인
     */
    public boolean isLocked() {
        return status == UserStatus.LOCKED;
    }
    
    /**
     * 특정 권한 보유 여부 확인
     */
    public boolean hasRole(String roleName) {
        return roles != null && roles.contains(roleName);
    }
    
    /**
     * UserRegisteredEvent로부터 UserView 생성
     */
    public static UserView fromUserRegistered(String userId, String username, String passwordHash, String name, 
                                            String email, String phone, Set<String> initialRoles, 
                                            Instant registeredAt, String registeredBy) {
        return UserView.builder()
                .userId(userId)
                .username(username)
                .passwordHash(passwordHash)
                .name(name)
                .email(email)
                .phone(phone)
                .status(UserStatus.ACTIVE)
                .roles(initialRoles)
                .failedLoginAttempts(0)
                .createdAt(registeredAt)
                .updatedAt(registeredAt)
                .registeredBy(registeredBy)
                .build();
    }
    
    /**
     * 로그인 성공 시 정보 업데이트
     */
    public void updateOnLoginSuccess(String sessionId, Instant loginTime) {
        this.failedLoginAttempts = 0;
        this.lastLoginAt = loginTime;
        this.activeSessionId = sessionId;
        this.sessionStartTime = loginTime;
        this.updatedAt = Instant.now();
    }
    
    /**
     * 로그인 실패 시 정보 업데이트
     */
    public void updateOnLoginFailure(int failedAttempts, boolean isAccountLocked) {
        this.failedLoginAttempts = failedAttempts;
        if (isAccountLocked) {
            this.status = UserStatus.LOCKED;
        }
        this.updatedAt = Instant.now();
    }
    
    /**
     * 로그아웃 시 세션 정보 클리어
     */
    public void clearSession() {
        this.activeSessionId = null;
        this.sessionStartTime = null;
        this.updatedAt = Instant.now();
    }
    
    /**
     * 권한 추가
     */
    public void addRole(String roleName) {
        if (this.roles != null) {
            this.roles.add(roleName);
            this.updatedAt = Instant.now();
        }
    }
    
    /**
     * 계정 잠금
     */
    public void lockAccount() {
        this.status = UserStatus.LOCKED;
        this.activeSessionId = null;
        this.sessionStartTime = null;
        this.updatedAt = Instant.now();
    }
    
    // 2FA 관련 메서드들
    
    /**
     * 2FA 활성화 여부 확인
     */
    public boolean isTwoFactorEnabled() {
        return Boolean.TRUE.equals(twoFactorEnabled) && totpSecretKey != null;
    }
    
    /**
     * 2FA 설정 활성화
     */
    public void enableTwoFactor(String secretKey, Set<String> backupCodeHashes) {
        this.twoFactorEnabled = true;
        this.totpSecretKey = secretKey;
        this.backupCodeHashes = backupCodeHashes;
        this.twoFactorSetupAt = Instant.now();
        this.updatedAt = Instant.now();
    }
    
    /**
     * 키움증권 계좌 할당
     */
    public void assignKiwoomAccount(String kiwoomAccountId, Instant assignedAt) {
        this.kiwoomAccountId = kiwoomAccountId;
        this.kiwoomAccountAssignedAt = assignedAt;
        this.kiwoomCredentialsUpdatedAt = assignedAt;
        this.updatedAt = Instant.now();
    }
    
    /**
     * 2FA 비활성화
     */
    public void disableTwoFactor() {
        this.twoFactorEnabled = false;
        this.totpSecretKey = null;
        this.backupCodeHashes = null;
        this.twoFactorSetupAt = null;
        this.updatedAt = Instant.now();
    }
    
    /**
     * 키움증권 인증 정보 업데이트
     */
    public void updateKiwoomCredentials(Instant updatedAt) {
        this.kiwoomCredentialsUpdatedAt = updatedAt;
        this.updatedAt = Instant.now();
    }
    
    /**
     * 백업 코드 사용 (사용한 코드 제거)
     */
    public boolean useBackupCode(String backupCodeHash) {
        if (backupCodeHashes != null && backupCodeHashes.contains(backupCodeHash)) {
            backupCodeHashes.remove(backupCodeHash);
            this.updatedAt = Instant.now();
            return true;
        }
        return false;
    }
    
    /**
     * 남은 백업 코드 수
     */
    public int getRemainingBackupCodesCount() {
        try {
            return backupCodeHashes != null ? backupCodeHashes.size() : 0;
        } catch (Exception e) {
            // LazyInitializationException이나 다른 Hibernate 관련 예외 처리
            return 0;
        }
    }
    
    /**
     * 키움증권 계좌 할당 취소
     */
    public void revokeKiwoomAccount() {
        this.kiwoomAccountId = null;
        this.kiwoomAccountAssignedAt = null;
        this.kiwoomCredentialsUpdatedAt = null;
        this.updatedAt = Instant.now();
    }
    
    /**
     * 키움증권 계좌 할당 여부 확인
     */
    public boolean hasKiwoomAccount() {
        return this.kiwoomAccountId != null && !this.kiwoomAccountId.trim().isEmpty();
    }
    
    /**
     * 키움증권 계좌 ID 반환
     */
    public String getKiwoomAccountId() {
        return this.kiwoomAccountId;
    }
}