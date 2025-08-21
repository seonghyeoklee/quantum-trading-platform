package com.quantum.trading.platform.query.view;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.UserStatus;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
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
}