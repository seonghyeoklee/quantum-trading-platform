package com.quantum.kis.service;

import com.quantum.kis.config.KisApiRateLimitConfig;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

/**
 * KIS API Rate Limiter - 중앙집중식 호출 제한 관리
 *
 * <p>공식 정책 준수: - 실전투자: 1초당 20건 (계좌별) - 모의투자: 1초당 2건 (계좌별) - 토큰발급: 1초당 1건
 *
 * <p>Thread-safe하며 동시 접근 시 안전한 Rate Limiting 제공
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class KisRateLimiter {

    private final KisApiRateLimitConfig config;

    // API 엔드포인트별 호출 통계
    private final ConcurrentHashMap<String, CallStatistics> callStats = new ConcurrentHashMap<>();

    // 전역 Lock (토큰 발급 등 특별한 경우)
    private final ReentrantLock globalLock = new ReentrantLock();

    /**
     * API 호출 전 Rate Limit 체크 및 허용 여부 반환
     *
     * @param apiEndpoint API 엔드포인트 식별자
     * @param isTokenRequest 토큰 발급 요청 여부 (별도 제한 적용)
     * @return 호출 허용 여부
     */
    public boolean tryAcquire(String apiEndpoint, boolean isTokenRequest) {
        try {
            if (isTokenRequest) {
                return tryAcquireTokenCall(apiEndpoint);
            } else {
                return tryAcquireRestCall(apiEndpoint);
            }
        } catch (Exception e) {
            log.error("Rate limiter error for {}: {}", apiEndpoint, e.getMessage());
            // 에러 발생시 보수적으로 허용 (시스템 중단 방지)
            return true;
        }
    }

    /**
     * 강제 대기 후 호출 허용 (재시도 로직)
     *
     * @param apiEndpoint API 엔드포인트 식별자
     * @param isTokenRequest 토큰 발급 요청 여부
     * @return 호출 허용 여부
     */
    public boolean acquireWithWait(String apiEndpoint, boolean isTokenRequest) {
        for (int attempt = 1; attempt <= config.getMaxRetryAttempts(); attempt++) {
            if (tryAcquire(apiEndpoint, isTokenRequest)) {
                if (attempt > 1) {
                    log.debug("Rate limiter success on attempt {} for {}", attempt, apiEndpoint);
                }
                return true;
            }

            if (attempt < config.getMaxRetryAttempts()) {
                try {
                    long waitTime = config.getWaitTimeOnLimitMs() * attempt;
                    log.debug(
                            "Rate limit exceeded for {}, waiting {}ms (attempt {})",
                            apiEndpoint,
                            waitTime,
                            attempt);
                    Thread.sleep(waitTime);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    log.warn("Rate limiter wait interrupted for {}", apiEndpoint);
                    return false;
                }
            }
        }

        log.warn(
                "Rate limiter failed after {} attempts for {}",
                config.getMaxRetryAttempts(),
                apiEndpoint);
        return false;
    }

    /** 일반 REST API 호출 제한 체크 */
    private boolean tryAcquireRestCall(String apiEndpoint) {
        CallStatistics stats = callStats.computeIfAbsent(apiEndpoint, k -> new CallStatistics());
        LocalDateTime now = LocalDateTime.now();

        synchronized (stats) {
            // 1. 초당 제한 체크
            if (!checkSecondLimit(stats, now, config.getRestCallsPerSecond())) {
                return false;
            }

            // 2. 분당 제한 체크
            if (!checkMinuteLimit(stats, now, config.getCallsPerMinute())) {
                return false;
            }

            // 3. 시간당 제한 체크
            if (!checkHourLimit(stats, now, config.getCallsPerHour())) {
                return false;
            }

            // 4. 호출 기록 업데이트
            stats.recordCall(now);
            return true;
        }
    }

    /** 토큰 발급 API 호출 제한 체크 (1초당 1건) */
    private boolean tryAcquireTokenCall(String apiEndpoint) {
        // 토큰 발급은 전역 Lock으로 더 엄격하게 관리
        if (!globalLock.tryLock()) {
            log.debug("Token request blocked due to global lock for {}", apiEndpoint);
            return false;
        }

        try {
            CallStatistics stats =
                    callStats.computeIfAbsent(apiEndpoint + "_token", k -> new CallStatistics());
            LocalDateTime now = LocalDateTime.now();

            synchronized (stats) {
                // 토큰 요청은 초당 1건만 허용
                if (!checkSecondLimit(stats, now, config.getTokenCallsPerSecond())) {
                    return false;
                }

                stats.recordCall(now);
                return true;
            }
        } finally {
            globalLock.unlock();
        }
    }

    /** 초당 호출 제한 체크 */
    private boolean checkSecondLimit(CallStatistics stats, LocalDateTime now, int maxCalls) {
        LocalDateTime oneSecondAgo = now.minus(1, ChronoUnit.SECONDS);
        long callsInLastSecond = stats.getCallsAfter(oneSecondAgo);

        if (callsInLastSecond >= maxCalls) {
            log.debug("Second limit exceeded: {} >= {}", callsInLastSecond, maxCalls);
            return false;
        }
        return true;
    }

    /** 분당 호출 제한 체크 */
    private boolean checkMinuteLimit(CallStatistics stats, LocalDateTime now, int maxCalls) {
        LocalDateTime oneMinuteAgo = now.minus(1, ChronoUnit.MINUTES);
        long callsInLastMinute = stats.getCallsAfter(oneMinuteAgo);

        if (callsInLastMinute >= maxCalls) {
            log.debug("Minute limit exceeded: {} >= {}", callsInLastMinute, maxCalls);
            return false;
        }
        return true;
    }

    /** 시간당 호출 제한 체크 */
    private boolean checkHourLimit(CallStatistics stats, LocalDateTime now, int maxCalls) {
        LocalDateTime oneHourAgo = now.minus(1, ChronoUnit.HOURS);
        long callsInLastHour = stats.getCallsAfter(oneHourAgo);

        if (callsInLastHour >= maxCalls) {
            log.warn("Hour limit exceeded: {} >= {}", callsInLastHour, maxCalls);
            return false;
        }
        return true;
    }

    /** API 호출 통계 조회 (모니터링용) */
    public RateLimitStatus getStatus(String apiEndpoint) {
        CallStatistics stats = callStats.get(apiEndpoint);
        if (stats == null) {
            return new RateLimitStatus(apiEndpoint, 0, 0, 0, true);
        }

        LocalDateTime now = LocalDateTime.now();
        synchronized (stats) {
            long callsLastSecond = stats.getCallsAfter(now.minus(1, ChronoUnit.SECONDS));
            long callsLastMinute = stats.getCallsAfter(now.minus(1, ChronoUnit.MINUTES));
            long callsLastHour = stats.getCallsAfter(now.minus(1, ChronoUnit.HOURS));

            boolean available =
                    callsLastSecond < config.getRestCallsPerSecond()
                            && callsLastMinute < config.getCallsPerMinute()
                            && callsLastHour < config.getCallsPerHour();

            return new RateLimitStatus(
                    apiEndpoint, callsLastSecond, callsLastMinute, callsLastHour, available);
        }
    }

    /** 전체 통계 초기화 (매일 자정 실행) */
    @Scheduled(cron = "0 0 0 * * *", zone = "Asia/Seoul")
    public void cleanupOldStatistics() {
        LocalDateTime cutoff =
                LocalDateTime.now().minus(config.getStatisticsRetentionHours(), ChronoUnit.HOURS);

        callStats
                .values()
                .forEach(
                        stats -> {
                            synchronized (stats) {
                                stats.cleanupOldCalls(cutoff);
                            }
                        });

        log.info("Rate limiter statistics cleanup completed - cutoff: {}", cutoff);
    }

    /** 호출 통계 내부 클래스 */
    private static class CallStatistics {
        private final ConcurrentHashMap<LocalDateTime, AtomicInteger> callCounts =
                new ConcurrentHashMap<>();

        void recordCall(LocalDateTime timestamp) {
            // 초 단위로 반올림하여 정확한 통계 관리
            LocalDateTime rounded = timestamp.truncatedTo(ChronoUnit.SECONDS);
            callCounts.computeIfAbsent(rounded, k -> new AtomicInteger(0)).incrementAndGet();
        }

        long getCallsAfter(LocalDateTime after) {
            return callCounts.entrySet().stream()
                    .filter(entry -> entry.getKey().isAfter(after))
                    .mapToLong(entry -> entry.getValue().get())
                    .sum();
        }

        void cleanupOldCalls(LocalDateTime cutoff) {
            callCounts.entrySet().removeIf(entry -> entry.getKey().isBefore(cutoff));
        }
    }

    /** Rate Limit 상태 정보 */
    public record RateLimitStatus(
            String apiEndpoint,
            long callsLastSecond,
            long callsLastMinute,
            long callsLastHour,
            boolean available) {}
}
