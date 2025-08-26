package com.quantum.trading.platform.query.service;

import com.quantum.trading.platform.query.repository.KiwoomAccountViewRepository;
import com.quantum.trading.platform.query.repository.KiwoomApiUsageLogViewRepository;
import com.quantum.trading.platform.query.view.KiwoomAccountView;
import com.quantum.trading.platform.query.view.KiwoomApiUsageLogView;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * 키움증권 계좌 조회 서비스
 * 
 * CQRS Query Side - 키움증권 계좌 정보 조회를 위한 비즈니스 서비스
 * Repository를 통해 View 데이터를 조회하고 비즈니스 로직 적용
 */
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class KiwoomAccountQueryService {

    private final KiwoomAccountViewRepository kiwoomAccountViewRepository;
    private final KiwoomApiUsageLogViewRepository apiUsageLogViewRepository;

    /**
     * 사용자의 키움증권 계좌 조회
     */
    public Optional<KiwoomAccountView> getUserKiwoomAccount(String userId) {
        log.debug("Querying Kiwoom account for user: {}", userId);
        return kiwoomAccountViewRepository.findActiveAccountByUserId(userId);
    }

    /**
     * 키움증권 계좌번호로 계좌 조회
     */
    public Optional<KiwoomAccountView> getKiwoomAccountById(String kiwoomAccountId) {
        log.debug("Querying Kiwoom account by ID: {}", kiwoomAccountId);
        return kiwoomAccountViewRepository.findByKiwoomAccountId(kiwoomAccountId);
    }

    /**
     * 모든 활성 키움증권 계좌 조회
     */
    public List<KiwoomAccountView> getAllActiveAccounts() {
        log.debug("Querying all active Kiwoom accounts");
        return kiwoomAccountViewRepository.findAllActiveAccounts();
    }

    /**
     * 사용자의 키움증권 계좌 할당 여부 확인
     */
    public boolean hasUserKiwoomAccount(String userId) {
        log.debug("Checking if user has Kiwoom account: {}", userId);
        return kiwoomAccountViewRepository.existsActiveAccountByUserId(userId);
    }

    /**
     * 키움증권 계좌번호 중복 확인
     */
    public boolean isKiwoomAccountIdExists(String kiwoomAccountId) {
        log.debug("Checking if Kiwoom account ID exists: {}", kiwoomAccountId);
        return kiwoomAccountViewRepository.existsByKiwoomAccountId(kiwoomAccountId);
    }

    /**
     * 최근 할당된 키움증권 계좌 조회
     */
    public List<KiwoomAccountView> getRecentlyAssignedAccounts(int days) {
        log.debug("Querying recently assigned accounts within {} days", days);
        Instant fromDate = Instant.now().minus(days, ChronoUnit.DAYS);
        return kiwoomAccountViewRepository.findAccountsAssignedAfter(fromDate);
    }

    /**
     * 인증 정보가 최근 업데이트된 계좌 조회
     */
    public List<KiwoomAccountView> getAccountsWithRecentCredentialUpdates(int days) {
        log.debug("Querying accounts with recent credential updates within {} days", days);
        Instant fromDate = Instant.now().minus(days, ChronoUnit.DAYS);
        return kiwoomAccountViewRepository.findAccountsWithRecentCredentialUpdates(fromDate);
    }

    /**
     * 계좌 통계 조회
     */
    public AccountStatistics getAccountStatistics() {
        log.debug("Querying account statistics");
        
        long totalAccounts = kiwoomAccountViewRepository.count();
        long activeAccounts = kiwoomAccountViewRepository.findAllActiveAccounts().size();
        long accountsWithValidCredentials = kiwoomAccountViewRepository.countAccountsWithValidCredentials();
        
        return AccountStatistics.builder()
                .totalAccounts(totalAccounts)
                .activeAccounts(activeAccounts)
                .inactiveAccounts(totalAccounts - activeAccounts)
                .accountsWithValidCredentials(accountsWithValidCredentials)
                .build();
    }

    /**
     * 사용자별 키움증권 계좌 할당 상태 배치 조회
     */
    public Map<String, Boolean> checkUsersKiwoomAccountStatus(List<String> userIds) {
        log.debug("Checking Kiwoom account status for {} users", userIds.size());
        
        List<String> usersWithAccounts = kiwoomAccountViewRepository.findUserIdsWithActiveAccounts(userIds);
        
        return userIds.stream()
                .collect(Collectors.toMap(
                        userId -> userId,
                        userId -> usersWithAccounts.contains(userId)
                ));
    }

    // API 사용 로그 관련 메서드들

    /**
     * 사용자의 API 사용 로그 조회 (페이징)
     */
    public Page<KiwoomApiUsageLogView> getUserApiUsageLogs(String userId, int page, int size) {
        log.debug("Querying API usage logs for user: {}, page: {}, size: {}", userId, page, size);
        Pageable pageable = PageRequest.of(page, size);
        return apiUsageLogViewRepository.findByUserIdOrderByUsageTimestampDesc(userId, pageable);
    }

    /**
     * 키움증권 계좌의 API 사용 로그 조회
     */
    public Page<KiwoomApiUsageLogView> getAccountApiUsageLogs(String kiwoomAccountId, int page, int size) {
        log.debug("Querying API usage logs for account: {}, page: {}, size: {}", kiwoomAccountId, page, size);
        Pageable pageable = PageRequest.of(page, size);
        return apiUsageLogViewRepository.findByKiwoomAccountIdOrderByUsageTimestampDesc(kiwoomAccountId, pageable);
    }

    /**
     * 사용자의 API 사용 통계 조회
     */
    public ApiUsageStatistics getUserApiUsageStatistics(String userId, int days) {
        log.debug("Querying API usage statistics for user: {} within {} days", userId, days);
        
        Instant fromDate = Instant.now().minus(days, ChronoUnit.DAYS);
        
        long successfulCalls = apiUsageLogViewRepository.countSuccessfulApiCallsByUserSince(userId, fromDate);
        long failedCalls = apiUsageLogViewRepository.countFailedApiCallsByUserSince(userId, fromDate);
        Double avgRequestSize = apiUsageLogViewRepository.getAverageRequestSizeByUser(userId, fromDate);
        
        return ApiUsageStatistics.builder()
                .userId(userId)
                .periodDays(days)
                .successfulCalls(successfulCalls)
                .failedCalls(failedCalls)
                .totalCalls(successfulCalls + failedCalls)
                .successRate(calculateSuccessRate(successfulCalls, failedCalls))
                .averageRequestSize(avgRequestSize != null ? avgRequestSize : 0.0)
                .build();
    }

    /**
     * 최근 실패한 API 호출 조회
     */
    public List<KiwoomApiUsageLogView> getRecentFailedApiCalls(int hours) {
        log.debug("Querying recent failed API calls within {} hours", hours);
        Instant fromDate = Instant.now().minus(hours, ChronoUnit.HOURS);
        return apiUsageLogViewRepository.findRecentFailedApiCalls(fromDate);
    }

    /**
     * 전체 시스템 API 사용 통계 조회
     */
    public List<Object[]> getDailyApiUsageStats(int days) {
        log.debug("Querying daily API usage statistics for {} days", days);
        Instant fromDate = Instant.now().minus(days, ChronoUnit.DAYS);
        return apiUsageLogViewRepository.getDailyApiUsageStats(fromDate);
    }

    /**
     * API 엔드포인트별 사용 통계 조회
     */
    public List<Object[]> getApiEndpointUsageStats(int days) {
        log.debug("Querying API endpoint usage statistics for {} days", days);
        Instant fromDate = Instant.now().minus(days, ChronoUnit.DAYS);
        return apiUsageLogViewRepository.getApiEndpointUsageStats(fromDate);
    }

    /**
     * 활성 사용자 목록 조회 (최근 API 사용한 사용자)
     */
    public List<String> getActiveUsers(int hours) {
        log.debug("Querying active users within {} hours", hours);
        Instant fromDate = Instant.now().minus(hours, ChronoUnit.HOURS);
        return apiUsageLogViewRepository.findActiveUsersSince(fromDate);
    }

    // Helper methods
    private double calculateSuccessRate(long successful, long failed) {
        long total = successful + failed;
        if (total == 0) return 0.0;
        return (double) successful / total * 100.0;
    }

    // Inner classes for statistics
    @lombok.Builder
    @lombok.Data
    public static class AccountStatistics {
        private long totalAccounts;
        private long activeAccounts;
        private long inactiveAccounts;
        private long accountsWithValidCredentials;
    }

    @lombok.Builder
    @lombok.Data
    public static class ApiUsageStatistics {
        private String userId;
        private int periodDays;
        private long successfulCalls;
        private long failedCalls;
        private long totalCalls;
        private double successRate;
        private double averageRequestSize;
    }
}