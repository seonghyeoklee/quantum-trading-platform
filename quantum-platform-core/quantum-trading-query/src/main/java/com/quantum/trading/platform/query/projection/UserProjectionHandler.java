package com.quantum.trading.platform.query.projection;

import com.quantum.trading.platform.query.repository.UserViewRepository;
import com.quantum.trading.platform.query.view.UserView;
import com.quantum.trading.platform.shared.event.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * User Projection Handler
 *
 * Domain Events를 구독하여 UserView Read Model을 업데이트
 * Event Sourcing의 Query Side 역할 수행
 */
@Component
@RequiredArgsConstructor
@Slf4j
@Transactional
public class UserProjectionHandler {

    private final UserViewRepository userViewRepository;

    /**
     * 사용자 등록 이벤트 처리
     */
    @EventHandler
    public void on(UserRegisteredEvent event) {
        log.info("Processing UserRegisteredEvent for user: {}", event.username());

        try {
            // 중복 체크
            if (userViewRepository.existsByUsername(event.username())) {
                log.warn("User already exists with username: {}", event.username());
                return;
            }

            if (userViewRepository.existsByEmail(event.email())) {
                log.warn("User already exists with email: {}", event.email());
                return;
            }

            // UserView 생성 및 저장
            UserView userView = UserView.fromUserRegistered(
                    event.userId().value(),
                    event.username(),
                    event.passwordHash(),
                    event.name(),
                    event.email(),
                    event.phone(),
                    event.initialRoles(),
                    event.registeredAt(),
                    event.registeredBy()
            );

            userViewRepository.save(userView);

            log.info("UserView created successfully for user: {} with ID: {}",
                    event.username(), event.userId().value());

        } catch (Exception e) {
            log.error("Failed to process UserRegisteredEvent for user: {}", event.username(), e);
            throw e;
        }
    }

    /**
     * 로그인 성공 이벤트 처리
     */
    @EventHandler
    public void on(UserLoginSucceededEvent event) {
        log.info("Processing UserLoginSucceededEvent for user: {}", event.username());

        try {
            UserView userView = userViewRepository.findById(event.userId().value())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for login success: " + event.userId().value()));

            userView.updateOnLoginSuccess(event.sessionId(), event.loginTime());
            userViewRepository.save(userView);

            log.info("UserView updated for successful login: {} with session: {}",
                    event.username(), event.sessionId());

        } catch (Exception e) {
            log.error("Failed to process UserLoginSucceededEvent for user: {}", event.username(), e);
            throw e;
        }
    }

    /**
     * 로그인 실패 이벤트 처리
     */
    @EventHandler
    public void on(UserLoginFailedEvent event) {
        log.info("Processing UserLoginFailedEvent for user: {} (attempt: {})",
                event.username(), event.failedAttempts());

        try {
            UserView userView = userViewRepository.findById(event.userId().value())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for login failure: " + event.userId().value()));

            userView.updateOnLoginFailure(event.failedAttempts(), event.accountLocked());
            userViewRepository.save(userView);

            if (event.accountLocked()) {
                log.warn("UserView updated - account locked for user: {} after {} failed attempts",
                        event.username(), event.failedAttempts());
            } else {
                log.info("UserView updated for failed login: {} (attempt: {})",
                        event.username(), event.failedAttempts());
            }

        } catch (Exception e) {
            log.error("Failed to process UserLoginFailedEvent for user: {}", event.username(), e);
            throw e;
        }
    }

    /**
     * 로그아웃 이벤트 처리
     */
    @EventHandler
    public void on(UserLoggedOutEvent event) {
        log.info("Processing UserLoggedOutEvent for user: {} (session: {})",
                event.username(), event.sessionId());

        try {
            UserView userView = userViewRepository.findById(event.userId().value())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for logout: " + event.userId().value()));

            userView.clearSession();
            userViewRepository.save(userView);

            log.info("UserView updated for logout: {} - session cleared", event.username());

        } catch (Exception e) {
            log.error("Failed to process UserLoggedOutEvent for user: {}", event.username(), e);
            throw e;
        }
    }

    /**
     * 사용자 권한 부여 이벤트 처리
     */
    @EventHandler
    public void on(UserRoleGrantedEvent event) {
        log.info("Processing UserRoleGrantedEvent for user: {} - role: {}",
                event.username(), event.roleName());

        try {
            UserView userView = userViewRepository.findById(event.userId().value())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for role grant: " + event.userId().value()));

            userView.addRole(event.roleName());
            userViewRepository.save(userView);

            log.info("UserView updated - role granted: {} to user: {}",
                    event.roleName(), event.username());

        } catch (Exception e) {
            log.error("Failed to process UserRoleGrantedEvent for user: {}", event.username(), e);
            throw e;
        }
    }

    /**
     * 계정 잠금 이벤트 처리
     */
    @EventHandler
    public void on(UserAccountLockedEvent event) {
        log.info("Processing UserAccountLockedEvent for user: {} - reason: {}",
                event.username(), event.reason());

        try {
            UserView userView = userViewRepository.findById(event.userId().value())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for account lock: " + event.userId().value()));

            userView.lockAccount();
            userViewRepository.save(userView);

            log.warn("UserView updated - account locked for user: {} - reason: {}",
                    event.username(), event.reason());

        } catch (Exception e) {
            log.error("Failed to process UserAccountLockedEvent for user: {}", event.username(), e);
            throw e;
        }
    }

    /**
     * 2FA 활성화 이벤트 처리
     */
    @EventHandler
    public void on(TwoFactorEnabledEvent event) {
        log.info("Processing TwoFactorEnabledEvent for user: {}", event.userId().value());

        try {
            UserView userView = userViewRepository.findById(event.userId().value())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for 2FA enable: " + event.userId().value()));

            userView.enableTwoFactor(event.totpSecretKey(), event.backupCodeHashes());
            userViewRepository.save(userView);

            log.info("UserView updated - 2FA enabled for user: {} with {} backup codes",
                    event.userId().value(), event.backupCodeHashes().size());

        } catch (Exception e) {
            log.error("Failed to process TwoFactorEnabledEvent for user: {}", event.userId().value(), e);
            throw e;
        }
    }

    /**
     * 2FA 비활성화 이벤트 처리
     */
    @EventHandler
    public void on(TwoFactorDisabledEvent event) {
        log.info("Processing TwoFactorDisabledEvent for user: {} - reason: {}",
                event.userId().value(), event.reason());

        try {
            UserView userView = userViewRepository.findById(event.userId().value())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for 2FA disable: " + event.userId().value()));

            userView.disableTwoFactor();
            userViewRepository.save(userView);

            log.info("UserView updated - 2FA disabled for user: {} - reason: {}",
                    event.userId().value(), event.reason());

        } catch (Exception e) {
            log.error("Failed to process TwoFactorDisabledEvent for user: {}", event.userId().value(), e);
            throw e;
        }
    }

    /**
     * 백업 코드 사용 이벤트 처리
     */
    @EventHandler
    public void on(BackupCodeUsedEvent event) {
        log.info("Processing BackupCodeUsedEvent for user: {} - remaining codes: {}",
                event.userId().value(), event.remainingBackupCodes());

        try {
            UserView userView = userViewRepository.findById(event.userId().value())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for backup code usage: " + event.userId().value()));

            boolean codeUsed = userView.useBackupCode(event.backupCodeHash());
            if (codeUsed) {
                userViewRepository.save(userView);
                log.info("UserView updated - backup code used for user: {}, remaining codes: {}",
                        event.userId().value(), userView.getRemainingBackupCodesCount());
            } else {
                log.warn("Backup code was not found in UserView for user: {}", event.userId().value());
            }

        } catch (Exception e) {
            log.error("Failed to process BackupCodeUsedEvent for user: {}", event.userId().value(), e);
            throw e;
        }
    }
}
