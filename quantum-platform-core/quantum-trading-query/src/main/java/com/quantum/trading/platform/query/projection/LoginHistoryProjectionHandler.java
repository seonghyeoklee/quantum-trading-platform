package com.quantum.trading.platform.query.projection;

import com.quantum.trading.platform.query.repository.LoginHistoryViewRepository;
import com.quantum.trading.platform.query.view.LoginHistoryView;
import com.quantum.trading.platform.shared.event.UserLoginFailedEvent;
import com.quantum.trading.platform.shared.event.UserLoginSucceededEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

/**
 * 로그인 이력 Projection Handler
 *
 * 로그인 관련 이벤트를 LoginHistoryView로 변환하여 저장
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class LoginHistoryProjectionHandler {

    private final LoginHistoryViewRepository loginHistoryRepository;

    /**
     * 로그인 성공 이벤트 처리
     */
    @EventHandler
    public void on(UserLoginSucceededEvent event) {
        log.info("Processing UserLoginSucceededEvent for user: {}", event.username());

        try {
            LoginHistoryView loginHistory = LoginHistoryView.createSuccessHistory(
                event.userId().value(),
                event.username(),
                event.sessionId(),
                event.ipAddress(),
                event.userAgent(),
                event.loginTime(),
                event.previousLoginTime()
            );

            LoginHistoryView saved = loginHistoryRepository.save(loginHistory);
            log.debug("Login success history saved with ID: {} for user: {}",
                     saved.getId(), event.username());

        } catch (Exception e) {
            log.error("Failed to save login success history for user: {}", event.username(), e);
        }
    }

    /**
     * 로그인 실패 이벤트 처리
     */
    @EventHandler
    public void on(UserLoginFailedEvent event) {
        log.info("Processing UserLoginFailedEvent for user: {} (attempts: {})",
                event.username(), event.failedAttempts());

        try {
            LoginHistoryView loginHistory = LoginHistoryView.createFailureHistory(
                event.userId() != null ? event.userId().value() : null,
                event.username(),
                event.reason(),
                event.ipAddress(),
                event.userAgent(),
                event.attemptTime(),
                event.failedAttempts(),
                event.accountLocked()
            );

            LoginHistoryView saved = loginHistoryRepository.save(loginHistory);
            log.debug("Login failure history saved with ID: {} for user: {} (reason: {})",
                     saved.getId(), event.username(), event.reason());

            // 계정 잠금된 경우 경고 로그
            if (event.accountLocked()) {
                log.warn("Account locked for user: {} after {} failed attempts",
                        event.username(), event.failedAttempts());
            }

        } catch (Exception e) {
            log.error("Failed to save login failure history for user: {}", event.username(), e);
        }
    }
}
