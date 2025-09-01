package com.quantum.trading.platform.query.projection;

import com.quantum.trading.platform.query.repository.KiwoomAccountViewRepository;
import com.quantum.trading.platform.query.repository.KiwoomApiUsageLogViewRepository;
import com.quantum.trading.platform.query.repository.UserViewRepository;
import com.quantum.trading.platform.query.view.KiwoomAccountView;
import com.quantum.trading.platform.query.view.KiwoomApiUsageLogView;
import com.quantum.trading.platform.shared.event.KiwoomAccountAssignedEvent;
import com.quantum.trading.platform.shared.event.KiwoomAccountRevokedEvent;
import com.quantum.trading.platform.shared.event.KiwoomApiUsageLoggedEvent;
import com.quantum.trading.platform.shared.event.KiwoomCredentialsUpdatedEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * 키움증권 계좌 관련 Event Handler
 *
 * Command Side에서 발생한 이벤트를 구독하여 Query Side View 업데이트
 * CQRS 패턴에서 Command와 Query 분리를 구현
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class KiwoomAccountProjectionHandler {

    private final KiwoomAccountViewRepository kiwoomAccountViewRepository;
    private final KiwoomApiUsageLogViewRepository apiUsageLogViewRepository;
    private final UserViewRepository userViewRepository;

    /**
     * 키움증권 계좌 할당 이벤트 처리
     */
    @EventHandler
    @Transactional
    public void on(KiwoomAccountAssignedEvent event) {
        log.info("Processing KiwoomAccountAssignedEvent for user: {}, account: {}",
                event.userId().value(), event.kiwoomAccountId().value());

        try {
            // 1. KiwoomAccountView 생성
            KiwoomAccountView kiwoomAccountView = KiwoomAccountView.create(
                    event.userId().value(),
                    event.kiwoomAccountId().value(),
                    event.clientId(),
                    event.clientSecret(),
                    event.assignedAt()
            );
            kiwoomAccountViewRepository.save(kiwoomAccountView);

            // 2. UserView 업데이트
            userViewRepository.findById(event.userId().value())
                    .ifPresentOrElse(
                            userView -> {
                                userView.assignKiwoomAccount(
                                        event.kiwoomAccountId().value(),
                                        event.assignedAt()
                                );
                                userViewRepository.save(userView);
                                log.info("Updated UserView with Kiwoom account assignment for user: {}",
                                        event.userId().value());
                            },
                            () -> log.warn("UserView not found for user: {}", event.userId().value())
                    );

            log.info("Successfully processed KiwoomAccountAssignedEvent for user: {}",
                    event.userId().value());

        } catch (Exception e) {
            log.error("Failed to process KiwoomAccountAssignedEvent for user: {}",
                    event.userId().value(), e);
            throw e; // Re-throw to trigger transaction rollback
        }
    }

    /**
     * 키움증권 인증 정보 업데이트 이벤트 처리
     */
    @EventHandler
    @Transactional
    public void on(KiwoomCredentialsUpdatedEvent event) {
        log.info("Processing KiwoomCredentialsUpdatedEvent for user: {}", event.userId().value());

        try {
            // 1. KiwoomAccountView 업데이트
            kiwoomAccountViewRepository.findByUserId(event.userId().value())
                    .ifPresentOrElse(
                            kiwoomAccountView -> {
                                kiwoomAccountView.updateCredentials(
                                        event.newClientId(),
                                        event.newClientSecret()
                                );
                                kiwoomAccountViewRepository.save(kiwoomAccountView);
                                log.info("Updated KiwoomAccountView credentials for user: {}",
                                        event.userId().value());
                            },
                            () -> log.warn("KiwoomAccountView not found for user: {}", event.userId().value())
                    );

            // 2. UserView 업데이트
            userViewRepository.findById(event.userId().value())
                    .ifPresentOrElse(
                            userView -> {
                                userView.updateKiwoomCredentials(event.updatedAt());
                                userViewRepository.save(userView);
                                log.info("Updated UserView with credentials update time for user: {}",
                                        event.userId().value());
                            },
                            () -> log.warn("UserView not found for user: {}", event.userId().value())
                    );

            log.info("Successfully processed KiwoomCredentialsUpdatedEvent for user: {}",
                    event.userId().value());

        } catch (Exception e) {
            log.error("Failed to process KiwoomCredentialsUpdatedEvent for user: {}",
                    event.userId().value(), e);
            throw e;
        }
    }

    /**
     * 키움증권 계좌 할당 취소 이벤트 처리
     */
    @EventHandler
    @Transactional
    public void on(KiwoomAccountRevokedEvent event) {
        log.info("Processing KiwoomAccountRevokedEvent for user: {}, account: {}, reason: {}",
                event.userId().value(), event.kiwoomAccountId().value(), event.reason());

        try {
            // 1. KiwoomAccountView 비활성화
            kiwoomAccountViewRepository.findByUserId(event.userId().value())
                    .ifPresentOrElse(
                            kiwoomAccountView -> {
                                kiwoomAccountView.revoke();
                                kiwoomAccountViewRepository.save(kiwoomAccountView);
                                log.info("Deactivated KiwoomAccountView for user: {}",
                                        event.userId().value());
                            },
                            () -> log.warn("KiwoomAccountView not found for user: {}", event.userId().value())
                    );

            // 2. UserView 업데이트
            userViewRepository.findById(event.userId().value())
                    .ifPresentOrElse(
                            userView -> {
                                userView.revokeKiwoomAccount();
                                userViewRepository.save(userView);
                                log.info("Updated UserView with Kiwoom account revocation for user: {}",
                                        event.userId().value());
                            },
                            () -> log.warn("UserView not found for user: {}", event.userId().value())
                    );

            log.info("Successfully processed KiwoomAccountRevokedEvent for user: {}",
                    event.userId().value());

        } catch (Exception e) {
            log.error("Failed to process KiwoomAccountRevokedEvent for user: {}",
                    event.userId().value(), e);
            throw e;
        }
    }

    /**
     * 키움증권 API 사용 로그 이벤트 처리
     */
    @EventHandler
    @Transactional
    public void on(KiwoomApiUsageLoggedEvent event) {
        log.debug("Processing KiwoomApiUsageLoggedEvent for user: {}, endpoint: {}, success: {}",
                event.userId().value(), event.apiEndpoint(), event.success());

        try {
            // API 사용 로그 생성
            KiwoomApiUsageLogView logView = KiwoomApiUsageLogView.create(
                    event.userId().value(),
                    event.kiwoomAccountId().value(),
                    event.apiEndpoint(),
                    event.requestSize(),
                    event.success(),
                    event.usageTimestamp()
            );

            apiUsageLogViewRepository.save(logView);

            log.debug("Successfully processed KiwoomApiUsageLoggedEvent for user: {}",
                    event.userId().value());

        } catch (Exception e) {
            log.error("Failed to process KiwoomApiUsageLoggedEvent for user: {}",
                    event.userId().value(), e);
            throw e;
        }
    }
}
