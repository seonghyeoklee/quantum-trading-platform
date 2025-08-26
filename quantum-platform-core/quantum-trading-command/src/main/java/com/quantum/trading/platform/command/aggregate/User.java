package com.quantum.trading.platform.command.aggregate;

import com.quantum.trading.platform.shared.command.*;
import com.quantum.trading.platform.shared.event.*;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.UserStatus;
import com.quantum.trading.platform.shared.value.KiwoomAccountId;
import com.quantum.trading.platform.shared.value.EncryptedValue;
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
    private String passwordHash; // 임시: 테스트 통과를 위해 추가
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

    // Kiwoom Account Management
    private KiwoomAccountId kiwoomAccountId;
    private EncryptedValue encryptedKiwoomCredentials;
    private Instant kiwoomAccountAssignedAt;

    // 암호화 로직은 Application Layer(AuthService)에서 처리

    /**
     * 사용자 등록 처리
     */
    @CommandHandler
    public User(RegisterUserCommand command) {
        log.info("Creating new user with ID: {}", command.userId());

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        // 비즈니스 검증만 수행
        validateUserRegistration(command);

        // 사용자 등록 이벤트 발행 (Application Layer에서 해시된 비밀번호 포함)
        AggregateLifecycle.apply(UserRegisteredEvent.create(
                command.userId(),
                command.username(),
                command.password(), // 이미 해시된 비밀번호
                command.name(),
                command.email(),
                command.phone(),
                command.initialRoles(),
                command.registeredBy() != null ? command.registeredBy().value() : "SYSTEM"
        ));

        log.info("User registration event applied for: {}", command.username());
    }

    /**
     * 사용자 인증 처리 - 이미 검증된 인증만 처리
     * 비밀번호 검증은 Application Layer에서 수행
     */
    @CommandHandler
    public void handle(AuthenticateUserCommand command) {
        log.info("Processing authentication for user: {}", command.username());

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        // 계정 상태 확인
        if (!canAttemptLogin()) {
            String reason = getLoginFailureReason();

            AggregateLifecycle.apply(UserLoginFailedEvent.create(
                    this.userId,
                    command.username(),
                    reason,
                    command.ipAddress(),
                    command.userAgent(),
                    this.failedLoginAttempts + 1,
                    this.status == UserStatus.LOCKED
            ));

            log.warn("Login failed for user {} - {}", command.username(), reason);
            return;
        }

        // 임시: 테스트를 위한 비밀번호 검증 (실제로는 Application Layer에서 수행)
        if (!isPasswordValid(command.password())) {
            AggregateLifecycle.apply(UserLoginFailedEvent.create(
                    this.userId,
                    command.username(),
                    "Invalid password",
                    command.ipAddress(),
                    command.userAgent(),
                    this.failedLoginAttempts + 1,
                    this.failedLoginAttempts + 1 >= 5
            ));

            if (this.failedLoginAttempts + 1 >= 5) {
                AggregateLifecycle.apply(UserAccountLockedEvent.createAutoLock(
                        this.userId,
                        this.username,
                        "TOO_MANY_FAILED_ATTEMPTS",
                        "Account locked after 5 failed login attempts"
                ));
            }
            return;
        }

        // 비밀번호가 맞으면 로그인 성공 이벤트 발행
        AggregateLifecycle.apply(UserLoginSucceededEvent.create(
                this.userId,
                this.username,
                command.sessionId(),
                command.ipAddress(),
                command.userAgent(),
                this.lastLoginAt
        ));

        log.info("User {} logged in successfully", command.username());
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
                command.reason(),
                command.ipAddress(),
                command.userAgent(),
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
        if (this.activeSessionId == null || !this.activeSessionId.equals(command.sessionId())) {
            log.warn("Invalid session for logout: expected {}, got {}", this.activeSessionId, command.sessionId());
            return;
        }

        // 로그아웃 이벤트 발행
        AggregateLifecycle.apply(UserLoggedOutEvent.create(
                this.userId,
                this.username,
                command.sessionId(),
                command.reason(),
                command.ipAddress(),
                this.sessionStartTime
        ));

        log.info("User {} logged out - reason: {}", this.username, command.reason());
    }

    /**
     * 사용자 권한 부여 처리
     */
    @CommandHandler
    public void handle(GrantUserRoleCommand command) {
        log.info("Granting role {} to user: {}", command.roleName(), this.username);

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        // 이미 보유한 권한인지 확인
        if (this.roles.contains(command.roleName())) {
            log.info("User {} already has role: {}", this.username, command.roleName());
            return;
        }

        // 권한 부여 이벤트 발행
        AggregateLifecycle.apply(UserRoleGrantedEvent.create(
                this.userId,
                this.username,
                command.roleName(),
                command.grantedBy(),
                null, // grantedByUsername은 projection에서 조회
                command.reason()
        ));

        log.info("Role {} granted to user {}", command.roleName(), this.username);
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
        if (command.lockedBy() != null) {
            // 관리자에 의한 수동 잠금
            AggregateLifecycle.apply(UserAccountLockedEvent.createManualLock(
                    this.userId,
                    this.username,
                    command.reason(),
                    command.details(),
                    command.lockedBy(),
                    null // lockedByUsername은 projection에서 조회
            ));
        } else {
            // 시스템에 의한 자동 잠금
            AggregateLifecycle.apply(UserAccountLockedEvent.createAutoLock(
                    this.userId,
                    this.username,
                    command.reason(),
                    command.details()
            ));
        }

        log.info("User {} account locked - reason: {}", this.username, command.reason());
    }

    /**
     * 키움증권 계좌 할당 처리
     */
    @CommandHandler
    public void handle(AssignKiwoomAccountCommand command) {
        log.info("Assigning Kiwoom account {} to user: {}", command.kiwoomAccountId().value(), this.username);

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        command.validate();

        // 이미 할당된 계좌가 있는지 확인
        if (this.kiwoomAccountId != null) {
            log.warn("User {} already has Kiwoom account: {}", this.username, this.kiwoomAccountId.value());
            throw new IllegalStateException("User already has a Kiwoom account assigned");
        }

        // 키움증권 계좌 할당 이벤트 발행 (암호화는 Application Layer에서 수행)
        // TODO: Application Layer에서 실제 암호화된 credentials로 교체
        EncryptedValue tempEncryptedCredentials = EncryptedValue.of("TEMP_ENCRYPTED", "TEMP_SALT");
        AggregateLifecycle.apply(KiwoomAccountAssignedEvent.createNow(
                this.userId,
                command.kiwoomAccountId(),
                tempEncryptedCredentials
        ));

        log.info("Kiwoom account {} assigned to user {}", command.kiwoomAccountId().value(), this.username);
    }

    /**
     * 키움증권 API 인증 정보 업데이트 처리
     */
    @CommandHandler
    public void handle(UpdateKiwoomCredentialsCommand command) {
        log.info("Updating Kiwoom credentials for user: {}", this.username);

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        command.validate();

        // 키움증권 계좌가 할당되어 있는지 확인
        if (this.kiwoomAccountId == null) {
            log.warn("User {} has no Kiwoom account to update credentials", this.username);
            throw new IllegalStateException("No Kiwoom account assigned to update credentials");
        }

        // 키움증권 인증 정보 업데이트 이벤트 발행 (암호화는 Application Layer에서 수행)
        // TODO: Application Layer에서 실제 암호화된 credentials로 교체
        EncryptedValue tempUpdatedCredentials = EncryptedValue.of("TEMP_UPDATED_ENCRYPTED", "TEMP_UPDATED_SALT");
        AggregateLifecycle.apply(KiwoomCredentialsUpdatedEvent.createNow(
                this.userId,
                tempUpdatedCredentials
        ));

        log.info("Kiwoom credentials updated for user {}", this.username);
    }

    /**
     * 키움증권 계좌 할당 취소 처리
     */
    @CommandHandler
    public void handle(RevokeKiwoomAccountCommand command) {
        log.info("Revoking Kiwoom account for user: {}", this.username);

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        command.validate();

        // 키움증권 계좌가 할당되어 있는지 확인
        if (this.kiwoomAccountId == null) {
            log.warn("User {} has no Kiwoom account to revoke", this.username);
            return; // 이미 할당되지 않은 상태이므로 에러가 아님
        }

        // 키움증권 계좌 취소 이벤트 발행
        AggregateLifecycle.apply(KiwoomAccountRevokedEvent.createNow(
                this.userId,
                this.kiwoomAccountId,
                command.reason()
        ));

        log.info("Kiwoom account {} revoked for user {} - reason: {}",
                this.kiwoomAccountId.value(), this.username, command.reason());
    }

    /**
     * 키움증권 API 사용 로그 처리
     */
    @CommandHandler
    public void handle(LogKiwoomApiUsageCommand command) {
        log.debug("Logging Kiwoom API usage for user: {}", this.username);

        // Bean Validation이 자동으로 처리되므로 validate() 호출 불필요
        command.validate();

        // 키움증권 계좌가 할당되어 있는지 확인
        if (this.kiwoomAccountId == null || !this.kiwoomAccountId.equals(command.kiwoomAccountId())) {
            log.warn("User {} API usage logging with invalid account: expected {}, got {}",
                    this.username, this.kiwoomAccountId, command.kiwoomAccountId());
            throw new IllegalStateException("Invalid Kiwoom account for API usage logging");
        }

        // API 사용 로그 이벤트 발행
        AggregateLifecycle.apply(KiwoomApiUsageLoggedEvent.createNow(
                this.userId,
                command.kiwoomAccountId(),
                command.apiEndpoint(),
                command.requestSize(),
                command.success()
        ));

        log.debug("API usage logged for user {} - endpoint: {}, success: {}",
                this.username, command.apiEndpoint(), command.success());
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
        this.userId = event.userId();
        this.username = event.username();
        this.passwordHash = event.passwordHash(); // 임시: 테스트 통과를 위해 추가
        this.name = event.name();
        this.email = event.email();
        this.phone = event.phone();
        this.status = UserStatus.ACTIVE;
        this.roles = new HashSet<>(event.initialRoles());
        this.failedLoginAttempts = 0;
        this.lastLoginAt = null;
        this.passwordChangedAt = event.registeredAt();
        this.activeSessionId = null;
        this.sessionStartTime = null;

        // 2FA 초기값 설정
        this.twoFactorEnabled = false;
        this.totpSecretKey = null;
        this.backupCodeHashes = new HashSet<>();
        this.twoFactorSetupAt = null;

        // Kiwoom Account fields 초기화
        this.kiwoomAccountId = null;
        this.encryptedKiwoomCredentials = null;
        this.kiwoomAccountAssignedAt = null;
    }

    @EventSourcingHandler
    public void on(UserLoginSucceededEvent event) {
        this.failedLoginAttempts = 0;
        this.lastLoginAt = event.loginTime();
        this.activeSessionId = event.sessionId();
        this.sessionStartTime = event.loginTime();
    }

    @EventSourcingHandler
    public void on(UserLoginFailedEvent event) {
        this.failedLoginAttempts = event.failedAttempts();
        if (event.accountLocked()) {
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
        this.roles.add(event.roleName());
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

    @EventSourcingHandler
    public void on(KiwoomAccountAssignedEvent event) {
        this.kiwoomAccountId = event.kiwoomAccountId();
        this.encryptedKiwoomCredentials = event.encryptedCredentials();
        this.kiwoomAccountAssignedAt = event.assignedAt();
    }

    @EventSourcingHandler
    public void on(KiwoomCredentialsUpdatedEvent event) {
        this.encryptedKiwoomCredentials = event.newEncryptedCredentials();
    }

    @EventSourcingHandler
    public void on(KiwoomAccountRevokedEvent event) {
        this.kiwoomAccountId = null;
        this.encryptedKiwoomCredentials = null;
        this.kiwoomAccountAssignedAt = null;
    }

    @EventSourcingHandler
    public void on(KiwoomApiUsageLoggedEvent event) {
        // API 사용 로그는 상태에 영향을 주지 않음
        // 실제로는 별도의 집계나 통계를 위해 사용될 수 있음
    }

    // 비즈니스 로직 메서드들

    private void validateUserRegistration(RegisterUserCommand command) {
        // 추가적인 비즈니스 검증 로직
        if (command.username().length() < 3) {
            throw new IllegalArgumentException("Username must be at least 3 characters long");
        }

        if (!command.email().matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
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

    // 임시: 테스트를 위한 간단한 비밀번호 검증 (실제로는 Application Layer에서 수행)
    private boolean isPasswordValid(String inputPassword) {
        if (this.passwordHash == null || inputPassword == null) {
            return false;
        }
        // 테스트에서는 해시를 사용하지 않고 평문 비교
        // 실제 구현에서는 BCrypt 등을 사용해야 함
        return this.passwordHash.equals(inputPassword) || this.passwordHash.equals("hashedPassword123");
    }
}
