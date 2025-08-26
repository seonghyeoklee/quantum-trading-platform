package com.quantum.trading.platform.query;

import com.quantum.trading.platform.query.repository.KiwoomAccountViewRepository;
import com.quantum.trading.platform.query.repository.KiwoomApiUsageLogViewRepository;
import com.quantum.trading.platform.query.service.KiwoomQueryService;
import com.quantum.trading.platform.query.view.KiwoomAccountView;
import com.quantum.trading.platform.query.view.KiwoomApiUsageLogView;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Kiwoom Securities API Integration End-to-End Tests
 * 
 * 키움증권 API 통합 시나리오 테스트
 * - 계좌 관리 플로우
 * - API 사용 로깅 및 모니터링
 * - 토큰 관리 및 갱신
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
public class KiwoomIntegrationTest {

    @Autowired
    private KiwoomAccountViewRepository accountRepository;

    @Autowired
    private KiwoomApiUsageLogViewRepository usageLogRepository;

    @Autowired
    private KiwoomQueryService kiwoomQueryService;

    @Test
    @DisplayName("사용자별 키움증권 계좌 조회")
    void testFindUserKiwoomAccount() {
        // Given
        String userId = "TEST_USER_001";
        KiwoomAccountView account = createTestAccount(userId);
        accountRepository.save(account);

        // When
        Optional<KiwoomAccountView> found = accountRepository.findByUserId(userId);

        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getUserId()).isEqualTo(userId);
        assertThat(found.get().getIsActive()).isTrue();
    }

    @Test
    @DisplayName("키움증권 계좌 ID로 계좌 정보 조회")
    void testFindByKiwoomAccountId() {
        // Given
        String kiwoomAccountId = "KIWOOM_ACC_001";
        KiwoomAccountView account = createTestAccount("USER_001");
        account.setKiwoomAccountId(kiwoomAccountId);
        accountRepository.save(account);

        // When
        Optional<KiwoomAccountView> found = accountRepository.findByKiwoomAccountId(kiwoomAccountId);

        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getKiwoomAccountId()).isEqualTo(kiwoomAccountId);
    }

    @Test
    @DisplayName("활성 계좌만 조회")
    void testFindActiveAccounts() {
        // Given
        KiwoomAccountView activeAccount = createTestAccount("USER_001");
        activeAccount.setIsActive(true);
        accountRepository.save(activeAccount);

        KiwoomAccountView inactiveAccount = createTestAccount("USER_002");
        inactiveAccount.setIsActive(false);
        accountRepository.save(inactiveAccount);

        // When
        List<KiwoomAccountView> activeAccounts = accountRepository.findByIsActiveOrderByAssignedAtDesc(true);

        // Then
        assertThat(activeAccounts).hasSize(1);
        assertThat(activeAccounts.get(0).getUserId()).isEqualTo("USER_001");
    }

    @Test
    @DisplayName("사용자별 API 사용 로그 조회")
    void testUserApiUsageLogs() {
        // Given
        String userId = "TEST_USER_001";
        createAndSaveUsageLogs(userId, 5);

        // When
        Page<KiwoomApiUsageLogView> logs = usageLogRepository.findByUserIdOrderByUsageTimestampDesc(
            userId, PageRequest.of(0, 10)
        );

        // Then
        assertThat(logs.getContent()).hasSize(5);
        assertThat(logs.getContent().get(0).getUserId()).isEqualTo(userId);
    }

    @Test
    @DisplayName("API 사용 성공률 계산")
    void testApiSuccessRate() {
        // Given
        String userId = "TEST_USER_001";
        Instant fromDate = Instant.now().minusSeconds(3600); // 1 hour ago

        // Create 7 successful and 3 failed API calls
        for (int i = 0; i < 7; i++) {
            KiwoomApiUsageLogView log = createUsageLog(userId, true);
            usageLogRepository.save(log);
        }
        for (int i = 0; i < 3; i++) {
            KiwoomApiUsageLogView log = createUsageLog(userId, false);
            usageLogRepository.save(log);
        }

        // When
        long successCount = usageLogRepository.countSuccessfulApiCallsByUserSince(userId, fromDate);
        long failureCount = usageLogRepository.countFailedApiCallsByUserSince(userId, fromDate);

        // Then
        assertThat(successCount).isEqualTo(7);
        assertThat(failureCount).isEqualTo(3);
        
        double successRate = (double) successCount / (successCount + failureCount) * 100;
        assertThat(successRate).isEqualTo(70.0);
    }

    @Test
    @DisplayName("API 엔드포인트별 사용 통계")
    void testApiEndpointUsageStats() {
        // Given
        Instant fromDate = Instant.now().minusSeconds(3600);
        
        // Create logs for different endpoints
        createAndSaveUsageLog("USER_001", "/api/stock", true);
        createAndSaveUsageLog("USER_001", "/api/stock", true);
        createAndSaveUsageLog("USER_002", "/api/stock", true);
        createAndSaveUsageLog("USER_001", "/api/order", true);
        createAndSaveUsageLog("USER_002", "/api/chart", true);

        // When
        List<Object[]> stats = usageLogRepository.getApiEndpointUsageStats(fromDate);

        // Then
        assertThat(stats).isNotEmpty();
        // Most used endpoint should be /api/stock with 3 calls
        assertThat(stats.get(0)[0]).isEqualTo("/api/stock");
        assertThat(stats.get(0)[1]).isEqualTo(3L);
    }

    @Test
    @DisplayName("최근 실패한 API 호출 조회")
    void testFindRecentFailedApiCalls() {
        // Given
        Instant fromDate = Instant.now().minusSeconds(3600);
        
        // Create some failed API calls
        for (int i = 0; i < 3; i++) {
            KiwoomApiUsageLogView log = createUsageLog("USER_" + i, false);
            log.setErrorMessage("Connection timeout");
            usageLogRepository.save(log);
        }

        // When
        List<KiwoomApiUsageLogView> failedCalls = usageLogRepository.findRecentFailedApiCalls(fromDate);

        // Then
        assertThat(failedCalls).hasSize(3);
        assertThat(failedCalls).allMatch(log -> !log.getSuccess());
        assertThat(failedCalls).allMatch(log -> "Connection timeout".equals(log.getErrorMessage()));
    }

    @Test
    @DisplayName("활성 사용자 조회")
    void testFindActiveUsers() {
        // Given
        Instant fromDate = Instant.now().minusSeconds(3600);
        
        // Create API usage for different users
        createAndSaveUsageLog("USER_001", "/api/stock", true);
        createAndSaveUsageLog("USER_002", "/api/order", true);
        createAndSaveUsageLog("USER_001", "/api/chart", true);
        createAndSaveUsageLog("USER_003", "/api/stock", true);

        // When
        List<String> activeUsers = usageLogRepository.findActiveUsersSince(fromDate);

        // Then
        assertThat(activeUsers).hasSize(3);
        assertThat(activeUsers).containsExactlyInAnyOrder("USER_001", "USER_002", "USER_003");
    }

    @Test
    @DisplayName("KiwoomQueryService를 통한 통합 조회")
    void testKiwoomQueryServiceIntegration() {
        // Given
        String userId = "TEST_USER_001";
        
        // Create account
        KiwoomAccountView account = createTestAccount(userId);
        accountRepository.save(account);
        
        // Create usage logs
        createAndSaveUsageLogs(userId, 10);

        // When
        Optional<KiwoomAccountView> foundAccount = kiwoomQueryService.getUserKiwoomAccount(userId);
        Page<KiwoomApiUsageLogView> usageLogs = kiwoomQueryService.getUserApiUsageLogs(
            userId, PageRequest.of(0, 5)
        );

        // Then
        assertThat(foundAccount).isPresent();
        assertThat(foundAccount.get().getUserId()).isEqualTo(userId);
        assertThat(usageLogs.getContent()).hasSize(5);
        assertThat(usageLogs.getTotalElements()).isEqualTo(10);
    }

    // Helper methods
    private KiwoomAccountView createTestAccount(String userId) {
        KiwoomAccountView account = new KiwoomAccountView();
        account.setUserId(userId);
        account.setKiwoomAccountId("KIWOOM_" + userId);
        account.setClientIdHash("encrypted_client_id");
        account.setClientSecretHash("encrypted_client_secret");
        account.setIsActive(true);
        account.setAssignedAt(Instant.now());
        account.setCredentialsUpdatedAt(Instant.now());
        account.setRevokedAt(null);
        account.setRevokedReason(null);
        return account;
    }

    private KiwoomApiUsageLogView createUsageLog(String userId, boolean success) {
        KiwoomApiUsageLogView log = new KiwoomApiUsageLogView();
        log.setUserId(userId);
        log.setKiwoomAccountId("KIWOOM_" + userId);
        log.setApiEndpoint("/api/stock");
        log.setHttpMethod("GET");
        log.setRequestSize(256L);
        log.setResponseSize(1024L);
        log.setResponseTimeMs(150);
        log.setSuccess(success);
        log.setErrorMessage(success ? null : "Error occurred");
        log.setUsageTimestamp(Instant.now());
        return log;
    }

    private void createAndSaveUsageLogs(String userId, int count) {
        for (int i = 0; i < count; i++) {
            KiwoomApiUsageLogView log = createUsageLog(userId, true);
            usageLogRepository.save(log);
        }
    }

    private void createAndSaveUsageLog(String userId, String endpoint, boolean success) {
        KiwoomApiUsageLogView log = createUsageLog(userId, success);
        log.setApiEndpoint(endpoint);
        usageLogRepository.save(log);
    }
}