package com.quantum.kis.infrastructure.adapter.out.notification;

import com.quantum.kis.application.port.out.NotificationPort;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * 로깅 기반 알림 어댑터
 * 현재는 로깅으로만 알림을 처리하지만, 향후 이메일, 슬랙 등으로 확장 가능
 */
@Component
public class LoggingNotificationAdapter implements NotificationPort {

    private static final Logger log = LoggerFactory.getLogger(LoggingNotificationAdapter.class);

    @Override
    public void notifyTokenRefreshed(KisEnvironment environment, TokenType tokenType) {
        log.info("🔄 토큰 재발급 알림 - 환경: {}, 타입: {}", environment, tokenType);
    }

    @Override
    public void notifyTokenExpired(KisEnvironment environment, TokenType tokenType) {
        log.warn("⚠️ 토큰 만료 알림 - 환경: {}, 타입: {}", environment, tokenType);
    }

    @Override
    public void notifyTokenIssueFailed(KisEnvironment environment, TokenType tokenType, String errorMessage) {
        log.error("❌ 토큰 발급 실패 알림 - 환경: {}, 타입: {}, 오류: {}", environment, tokenType, errorMessage);
    }
}