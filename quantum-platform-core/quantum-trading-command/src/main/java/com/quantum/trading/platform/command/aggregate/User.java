package com.quantum.trading.platform.command.aggregate;

import com.quantum.trading.platform.shared.command.*;
import com.quantum.trading.platform.shared.event.*;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.UserStatus;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateLifecycle;
import org.axonframework.spring.stereotype.Aggregate;

import java.time.Instant;
import java.util.HashSet;
import java.util.Set;

/**
 * User Aggregate
 *
 * 사용자 도메인의 핵심 비즈니스 로직을 담당하는 Aggregate
 * Event Sourcing을 통해 사용자의 모든 상태 변경을 이벤트로 관리
 */
@Aggregate
@NoArgsConstructor
@Slf4j
public class User {

    @AggregateIdentifier
    private UserId userId;
    private String username;
    // 비밀번호는 Application Layer에서 검증하므로 Aggregate에서 제거
    private String name;
    private String email;
    private String phone;
    private UserStatus status;
    private Set<String> roles;
    private int failedLoginAttempts;
    private Instant lastLoginAt;
    private Instant passwordChangedAt;
    private String activeSessionId;
    private Instant sessionStartTime;
    
    // 2FA 관련 필드들
    private boolean twoFactorEnabled;
    private String totpSecretKey;
    private Set<String> backupCodeHashes;
    private Instant twoFactorSetupAt;

    // 암호화 로직은 Application Layer(AuthService)에서 처리

    /**
     * 사용자 등록 처리
     */
    @CommandHandler
    public User(RegisterUserCommand command) {
        log.info("Creating new user with ID: {}", command.getUserId());

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        // 비즈니스 검증만 수행
        validateUserRegistration(command);

        // 사용자 등록 이벤트 발행 (Application Layer에서 해시된 비밀번호 포함)
        AggregateLifecycle.apply(UserRegisteredEvent.create(
                command.getUserId(),
                command.getUsername(),
                command.getPassword(), // 이미 해시된 비밀번호
                command.getName(),
                command.getEmail(),
                command.getPhone(),
                command.getInitialRoles(),
                command.getRegisteredBy() != null ? command.getRegisteredBy().getValue() : "SYSTEM"
        ));

        log.info("User registration event applied for: {}", command.getUsername());
    }

    /**
     * 사용자 인증 처리 - 이미 검증된 인증만 처리
     * 비밀번호 검증은 Application Layer에서 수행
     */
    @CommandHandler
    public void handle(AuthenticateUserCommand command) {
        log.info("Processing authentication for user: {}", command.getUsername());

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        // 계정 상태 확인
        if (!canAttemptLogin()) {
            String reason = getLoginFailureReason();

            AggregateLifecycle.apply(UserLoginFailedEvent.create(
                    this.userId,
                    command.getUsername(),
                    reason,
                    command.getIpAddress(),
                    command.getUserAgent(),
                    this.failedLoginAttempts + 1,
                    this.status == UserStatus.LOCKED
            ));

            log.warn("Login failed for user {} - {}", command.getUsername(), reason);
            return;
        }

        // Application Layer에서 이미 비밀번호 검증이 완료됨 - 로그인 성공 이벤트 발행
        AggregateLifecycle.apply(UserLoginSucceededEvent.create(
                this.userId,
                this.username,
                command.getSessionId(),
                command.getIpAddress(),
                command.getUserAgent(),
                this.lastLoginAt
        ));

        log.info("User {} logged in successfully", command.getUsername());
    }

    /**
     * 로그인 실패 처리 - Application Layer에서 호출
     */
    @CommandHandler
    public void handle(RecordLoginFailureCommand command) {
        log.info("Recording login failure for user: {}", this.username);

        // 로그인 실패 횟수 증가
        boolean willBeLocked = (this.failedLoginAttempts + 1) >= 5;

        AggregateLifecycle.apply(UserLoginFailedEvent.create(
                this.userId,
                this.username,
                command.getReason(),
                command.getIpAddress(),
                command.getUserAgent(),
                this.failedLoginAttempts + 1,
                willBeLocked
        ));

        // 5회 실패 시 계정 잠금
        if (willBeLocked) {
            AggregateLifecycle.apply(UserAccountLockedEvent.createAutoLock(
                    this.userId,
                    this.username,
                    "TOO_MANY_FAILED_ATTEMPTS",
                    "Account locked after 5 failed login attempts"
            ));
        }

        log.warn("Login failure recorded for user: {}, attempts: {}", this.username, this.failedLoginAttempts + 1);
    }

    /**
     * 사용자 로그아웃 처리
     */
    @CommandHandler
    public void handle(LogoutUserCommand command) {
        log.info("Processing logout for user: {}", this.username);

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        // 활성 세션 확인
        if (this.activeSessionId == null || !this.activeSessionId.equals(command.getSessionId())) {
            log.warn("Invalid session for logout: expected {}, got {}", this.activeSessionId, command.getSessionId());
            return;
        }

        // 로그아웃 이벤트 발행
        AggregateLifecycle.apply(UserLoggedOutEvent.create(
                this.userId,
                this.username,
                command.getSessionId(),
                command.getReason(),
                command.getIpAddress(),
                this.sessionStartTime
        ));

        log.info("User {} logged out - reason: {}", this.username, command.getReason());
    }

    /**
     * 사용자 권한 부여 처리
     */
    @CommandHandler
    public void handle(GrantUserRoleCommand command) {
        log.info("Granting role {} to user: {}", command.getRoleName(), this.username);

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        // 이미 보유한 권한인지 확인
        if (this.roles.contains(command.getRoleName())) {
            log.info("User {} already has role: {}", this.username, command.getRoleName());
            return;
        }

        // 권한 부여 이벤트 발행
        AggregateLifecycle.apply(UserRoleGrantedEvent.create(
                this.userId,
                this.username,
                command.getRoleName(),
                command.getGrantedBy(),
                null, // grantedByUsername은 projection에서 조회
                command.getReason()
        ));

        log.info("Role {} granted to user {}", command.getRoleName(), this.username);
    }

    /**
     * 계정 잠금 처리
     */
    @CommandHandler
    public void handle(LockUserAccountCommand command) {
        log.info("Locking account for user: {}", this.username);

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        // 이미 잠긴 계정인지 확인
        if (this.status == UserStatus.LOCKED) {
            log.info("User {} account is already locked", this.username);
            return;
        }

        // 계정 잠금 이벤트 발행
        if (command.getLockedBy() != null) {
            // 관리자에 의한 수동 잠금
            AggregateLifecycle.apply(UserAccountLockedEvent.createManualLock(
                    this.userId,
                    this.username,
                    command.getReason(),
                    command.getDetails(),
                    command.getLockedBy(),
                    null // lockedByUsername은 projection에서 조회
            ));
        } else {
            // 시스템에 의한 자동 잠금
            AggregateLifecycle.apply(UserAccountLockedEvent.createAutoLock(
                    this.userId,
                    this.username,
                    command.getReason(),
                    command.getDetails()
            ));
        }

        log.info("User {} account locked - reason: {}", this.username, command.getReason());
    }

    /**
     * 2FA 활성화 처리
     */
    @CommandHandler
    public void handle(EnableTwoFactorCommand command) {
        log.info("Enabling 2FA for user: {}", this.username);
        
        command.validate();
        
        // 이미 2FA가 활성화된 경우
        if (this.twoFactorEnabled) {
            log.info("2FA is already enabled for user: {}", this.username);
            return;
        }
        
        // 계정 상태 확인
        if (this.status != UserStatus.ACTIVE) {
            throw new IllegalStateException("Cannot enable 2FA for inactive account");
        }
        
        // 2FA 활성화 이벤트 발행
        AggregateLifecycle.apply(TwoFactorEnabledEvent.of(
            this.userId,
            command.totpSecretKey(),
            command.backupCodeHashes()
        ));
        
        log.info("2FA enabled successfully for user: {}", this.username);
    }
    
    /**
     * 2FA 비활성화 처리
     */
    @CommandHandler
    public void handle(DisableTwoFactorCommand command) {
        log.info("Disabling 2FA for user: {}", this.username);
        
        command.validate();
        
        // 2FA가 비활성화된 경우
        if (!this.twoFactorEnabled) {
            log.info("2FA is already disabled for user: {}", this.username);
            return;
        }
        
        // 2FA 비활성화 이벤트 발행
        AggregateLifecycle.apply(TwoFactorDisabledEvent.of(
            this.userId,
            command.reason()
        ));
        
        log.info("2FA disabled successfully for user: {}", this.username);
    }
    
    /**
     * 백업 코드 사용 처리
     */
    @CommandHandler
    public void handle(UseBackupCodeCommand command) {
        log.info("Using backup code for user: {}", this.username);
        
        command.validate();
        
        // 2FA가 활성화되지 않은 경우
        if (!this.twoFactorEnabled) {
            throw new IllegalStateException("2FA is not enabled for this account");
        }
        
        // 백업 코드가 존재하는지 확인
        if (!this.backupCodeHashes.contains(command.backupCodeHash())) {
            throw new IllegalArgumentException("Invalid backup code");
        }
        
        // 백업 코드 사용 이벤트 발행
        int remainingCodes = this.backupCodeHashes.size() - 1;
        AggregateLifecycle.apply(BackupCodeUsedEvent.of(
            this.userId,
            command.backupCodeHash(),
            command.ipAddress(),
            command.userAgent(),
            remainingCodes
        ));
        
        log.info("Backup code used successfully for user: {}, remaining codes: {}", 
                this.username, remainingCodes);
    }

    // Event Sourcing Handlers - 상태 복원 로직

    @EventSourcingHandler
    public void on(UserRegisteredEvent event) {
        this.userId = event.getUserId();
        this.username = event.getUsername();
        // 비밀번호 해시는 Application Layer에서 관리하므로 Aggregate에서 제거
        this.name = event.getName();
        this.email = event.getEmail();
        this.phone = event.getPhone();
        this.status = UserStatus.ACTIVE;
        this.roles = new HashSet<>(event.getInitialRoles());
        this.failedLoginAttempts = 0;
        this.lastLoginAt = null;
        this.passwordChangedAt = event.getRegisteredAt();
        this.activeSessionId = null;
        this.sessionStartTime = null;
        
        // 2FA 초기값 설정
        this.twoFactorEnabled = false;
        this.totpSecretKey = null;
        this.backupCodeHashes = new HashSet<>();
        this.twoFactorSetupAt = null;
    }

    @EventSourcingHandler
    public void on(UserLoginSucceededEvent event) {
        this.failedLoginAttempts = 0;
        this.lastLoginAt = event.getLoginTime();
        this.activeSessionId = event.getSessionId();
        this.sessionStartTime = event.getLoginTime();
    }

    @EventSourcingHandler
    public void on(UserLoginFailedEvent event) {
        this.failedLoginAttempts = event.getFailedAttempts();
        if (event.isAccountLocked()) {
            this.status = UserStatus.LOCKED;
        }
    }

    @EventSourcingHandler
    public void on(UserLoggedOutEvent event) {
        this.activeSessionId = null;
        this.sessionStartTime = null;
    }

    @EventSourcingHandler
    public void on(UserRoleGrantedEvent event) {
        this.roles.add(event.getRoleName());
    }

    @EventSourcingHandler
    public void on(UserAccountLockedEvent event) {
        this.status = UserStatus.LOCKED;
    }
    
    // 2FA Event Sourcing Handlers
    
    @EventSourcingHandler
    public void on(TwoFactorEnabledEvent event) {
        this.twoFactorEnabled = true;
        this.totpSecretKey = event.totpSecretKey();
        this.backupCodeHashes = new HashSet<>(event.backupCodeHashes());
        this.twoFactorSetupAt = event.enabledAt();
    }
    
    @EventSourcingHandler
    public void on(TwoFactorDisabledEvent event) {
        this.twoFactorEnabled = false;
        this.totpSecretKey = null;
        this.backupCodeHashes.clear();
        this.twoFactorSetupAt = null;
    }
    
    @EventSourcingHandler
    public void on(BackupCodeUsedEvent event) {
        this.backupCodeHashes.remove(event.backupCodeHash());
    }

    // 비즈니스 로직 메서드들

    private void validateUserRegistration(RegisterUserCommand command) {
        // 추가적인 비즈니스 검증 로직
        if (command.getUsername().length() < 3) {
            throw new IllegalArgumentException("Username must be at least 3 characters long");
        }

        if (!command.getEmail().matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
            throw new IllegalArgumentException("Invalid email format");
        }
    }

    private boolean canAttemptLogin() {
        return this.status == UserStatus.ACTIVE && this.failedLoginAttempts < 5;
    }

    private String getLoginFailureReason() {
        if (this.status == UserStatus.LOCKED) {
            return "Account is locked";
        }
        if (this.status == UserStatus.INACTIVE) {
            return "Account is inactive";
        }
        if (this.status == UserStatus.DELETED) {
            return "Account is deleted";
        }
        if (this.failedLoginAttempts >= 5) {
            return "Too many failed attempts";
        }
        return "Unknown error";
    }
}
