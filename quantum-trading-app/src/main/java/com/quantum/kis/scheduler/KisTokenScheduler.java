package com.quantum.kis.scheduler;

import com.quantum.kis.service.KisTokenManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * KIS 토큰 자동 재발급 스케줄러
 */
@Component
@ConditionalOnProperty(name = "kis.scheduler.enabled", havingValue = "true", matchIfMissing = true)
public class KisTokenScheduler {

    private static final Logger log = LoggerFactory.getLogger(KisTokenScheduler.class);

    private final KisTokenManager tokenManager;

    public KisTokenScheduler(KisTokenManager tokenManager) {
        this.tokenManager = tokenManager;
    }

    /**
     * 매일 오전 9시에 모든 토큰을 재발급한다.
     * - KRX 개장 전 토큰을 미리 준비
     * - cron: "0 0 9 * * ?" (초 분 시 일 월 요일)
     */
    @Scheduled(cron = "0 0 9 * * ?")
    public void refreshAllTokensDaily() {
        log.info("=== 일일 토큰 재발급 스케줄 시작 ===");

        try {
            tokenManager.refreshAllTokens();
            log.info("=== 일일 토큰 재발급 스케줄 완료 ===");
        } catch (Exception e) {
            log.error("=== 일일 토큰 재발급 스케줄 실패 ===", e);
        }
    }

    /**
     * 4시간마다 만료된 토큰들을 정리한다.
     * - fixedRate: 4시간 (4 * 60 * 60 * 1000 = 14400000ms)
     */
    @Scheduled(fixedRate = 14400000)
    public void cleanupExpiredTokens() {
        log.debug("만료된 토큰 정리 스케줄 시작");

        try {
            tokenManager.cleanupExpiredTokens();
            log.debug("만료된 토큰 정리 스케줄 완료");
        } catch (Exception e) {
            log.error("만료된 토큰 정리 스케줄 실패", e);
        }
    }

    /**
     * 1시간마다 토큰 상태를 점검한다.
     * - fixedRate: 1시간 (60 * 60 * 1000 = 3600000ms)
     */
    @Scheduled(fixedRate = 3600000)
    public void checkTokenStatus() {
        log.debug("토큰 상태 점검 스케줄 시작");

        try {
            var tokenStatus = tokenManager.getTokenCacheStatus();

            if (tokenStatus.isEmpty()) {
                log.info("캐시된 토큰이 없습니다. 필요시 자동으로 발급됩니다.");
                return;
            }

            tokenStatus.forEach((key, tokenInfo) -> {
                if (tokenInfo.isValid()) {
                    if (tokenInfo.isExpiringSoon()) {
                        log.info("토큰 만료 임박 - {}: {} (만료: {})",
                            key, tokenInfo.tokenType(), tokenInfo.expiresAt());
                    } else {
                        log.debug("토큰 정상 - {}: {} (만료: {})",
                            key, tokenInfo.tokenType(), tokenInfo.expiresAt());
                    }
                } else {
                    log.warn("무효한 토큰 발견 - {}: {}", key, tokenInfo.tokenType());
                }
            });

            log.debug("토큰 상태 점검 스케줄 완료 - 총 {}개 토큰", tokenStatus.size());

        } catch (Exception e) {
            log.error("토큰 상태 점검 스케줄 실패", e);
        }
    }

    /**
     * 애플리케이션 시작 5분 후 초기 토큰을 발급한다.
     * - initialDelay: 5분 (5 * 60 * 1000 = 300000ms)
     * - fixedDelay: 실행되지 않음 (Long.MAX_VALUE)
     */
    @Scheduled(initialDelay = 300000, fixedDelay = Long.MAX_VALUE)
    public void initializeTokensOnStartup() {
        log.info("=== 애플리케이션 시작 시 토큰 초기화 시작 ===");

        try {
            tokenManager.refreshAllTokens();
            log.info("=== 애플리케이션 시작 시 토큰 초기화 완료 ===");
        } catch (Exception e) {
            log.error("=== 애플리케이션 시작 시 토큰 초기화 실패 ===", e);
        }
    }
}