package com.quantum.web.service;

import com.quantum.trading.platform.query.service.KiwoomAccountQueryService;
import com.quantum.trading.platform.query.view.KiwoomAccountView;
import com.quantum.trading.platform.shared.command.AssignKiwoomAccountCommand;
import com.quantum.trading.platform.shared.command.RevokeKiwoomAccountCommand;
import com.quantum.trading.platform.shared.command.UpdateKiwoomCredentialsCommand;
import com.quantum.trading.platform.shared.value.ApiCredentials;
import com.quantum.trading.platform.shared.value.EncryptedValue;
import com.quantum.trading.platform.shared.value.KiwoomAccountId;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

/**
 * 키움증권 계정 관리 Application Service
 * 
 * CQRS Command/Query 분리와 암호화, 토큰 관리를 통합한 고수준 비즈니스 서비스
 * - 키움증권 계정 할당/취소/업데이트
 * - 암호화된 인증 정보 관리
 * - 토큰 라이프사이클 관리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class KiwoomAccountManagementService {

    private final CommandGateway commandGateway;
    private final KiwoomAccountQueryService kiwoomAccountQueryService;
    private final EncryptionService encryptionService;
    private final KiwoomTokenService tokenService;

    /**
     * 사용자에게 키움증권 계정 할당
     */
    @Transactional
    public void assignKiwoomAccount(String userId, String kiwoomAccountId, String clientId, String clientSecret) {
        try {
            log.info("Assigning Kiwoom account {} to user {}", kiwoomAccountId, userId);

            // 1. 입력값 검증
            validateAssignmentInput(userId, kiwoomAccountId, clientId, clientSecret);

            // 2. 비즈니스 규칙 검증
            validateAssignmentBusinessRules(userId, kiwoomAccountId);

            // 3. API credentials 암호화
            ApiCredentials credentials = ApiCredentials.of(clientId, clientSecret);
            EncryptedValue encryptedCredentials = encryptionService.encryptApiCredentials(credentials);

            // 4. Command 전송 - 실제 암호화된 값으로 이벤트 업데이트
            AssignKiwoomAccountCommand command = new AssignKiwoomAccountCommand(
                    UserId.of(userId),
                    KiwoomAccountId.of(kiwoomAccountId),
                    credentials
            );

            commandGateway.sendAndWait(command);

            // 5. 성공 로그
            log.info("Successfully assigned Kiwoom account {} to user {}", kiwoomAccountId, userId);

        } catch (Exception e) {
            log.error("Failed to assign Kiwoom account {} to user {}", kiwoomAccountId, userId, e);
            throw new KiwoomAccountManagementException("Failed to assign Kiwoom account", e);
        }
    }

    /**
     * 키움증권 API 인증 정보 업데이트
     */
    @Transactional
    public void updateKiwoomCredentials(String userId, String newClientId, String newClientSecret) {
        try {
            log.info("Updating Kiwoom credentials for user {}", userId);

            // 1. 사용자의 키움증권 계정 확인
            if (!kiwoomAccountQueryService.hasUserKiwoomAccount(userId)) {
                throw new KiwoomAccountManagementException("User has no Kiwoom account to update");
            }

            // 2. 새로운 credentials 암호화
            ApiCredentials newCredentials = ApiCredentials.of(newClientId, newClientSecret);
            EncryptedValue encryptedCredentials = encryptionService.encryptApiCredentials(newCredentials);

            // 3. Command 전송
            UpdateKiwoomCredentialsCommand command = new UpdateKiwoomCredentialsCommand(
                    UserId.of(userId),
                    newCredentials
            );

            commandGateway.sendAndWait(command);

            // 4. 기존 토큰 무효화
            Optional<KiwoomAccountView> accountOpt = kiwoomAccountQueryService.getUserKiwoomAccount(userId);
            if (accountOpt.isPresent()) {
                tokenService.invalidateToken(userId, accountOpt.get().getKiwoomAccountId());
                log.info("Invalidated existing tokens for user {} after credential update", userId);
            }

            log.info("Successfully updated Kiwoom credentials for user {}", userId);

        } catch (Exception e) {
            log.error("Failed to update Kiwoom credentials for user {}", userId, e);
            throw new KiwoomAccountManagementException("Failed to update Kiwoom credentials", e);
        }
    }

    /**
     * 키움증권 계정 할당 취소
     */
    @Transactional
    public void revokeKiwoomAccount(String userId, String reason) {
        try {
            log.info("Revoking Kiwoom account for user {}, reason: {}", userId, reason);

            // 1. 사용자의 키움증권 계정 확인
            Optional<KiwoomAccountView> accountOpt = kiwoomAccountQueryService.getUserKiwoomAccount(userId);
            if (accountOpt.isEmpty()) {
                log.warn("User {} has no Kiwoom account to revoke", userId);
                return; // 이미 할당되지 않은 상태
            }

            KiwoomAccountView account = accountOpt.get();

            // 2. 토큰 무효화
            tokenService.invalidateToken(userId, account.getKiwoomAccountId());

            // 3. Command 전송
            RevokeKiwoomAccountCommand command = new RevokeKiwoomAccountCommand(
                    UserId.of(userId),
                    reason
            );

            commandGateway.sendAndWait(command);

            log.info("Successfully revoked Kiwoom account {} for user {}", 
                    account.getKiwoomAccountId(), userId);

        } catch (Exception e) {
            log.error("Failed to revoke Kiwoom account for user {}", userId, e);
            throw new KiwoomAccountManagementException("Failed to revoke Kiwoom account", e);
        }
    }

    /**
     * 키움증권 API 토큰 조회 (복호화된 credentials 사용)
     */
    public Optional<String> getKiwoomApiToken(String userId) {
        try {
            log.debug("Getting Kiwoom API token for user {}", userId);

            // 1. 사용자의 키움증권 계정 조회
            Optional<KiwoomAccountView> accountOpt = kiwoomAccountQueryService.getUserKiwoomAccount(userId);
            if (accountOpt.isEmpty()) {
                log.debug("User {} has no Kiwoom account", userId);
                return Optional.empty();
            }

            KiwoomAccountView account = accountOpt.get();

            // 2. Redis에서 토큰 조회
            Optional<String> tokenOpt = tokenService.getToken(userId, account.getKiwoomAccountId());
            
            if (tokenOpt.isPresent()) {
                log.debug("Found cached token for user {}", userId);
                return tokenOpt;
            }

            // 3. 토큰이 없거나 만료된 경우 새로 발급
            log.debug("No valid token found, attempting to refresh for user {}", userId);
            return refreshKiwoomApiToken(userId, account);

        } catch (Exception e) {
            log.error("Failed to get Kiwoom API token for user {}", userId, e);
            return Optional.empty();
        }
    }

    /**
     * 사용자 키움증권 계정 정보 조회
     */
    public Optional<KiwoomAccountInfo> getUserKiwoomAccountInfo(String userId) {
        try {
            log.debug("Getting Kiwoom account info for user {}", userId);

            Optional<KiwoomAccountView> accountOpt = kiwoomAccountQueryService.getUserKiwoomAccount(userId);
            if (accountOpt.isEmpty()) {
                return Optional.empty();
            }

            KiwoomAccountView account = accountOpt.get();

            // 토큰 정보 조회
            Optional<KiwoomTokenService.TokenInfo> tokenInfoOpt = 
                    tokenService.getTokenInfo(userId, account.getKiwoomAccountId());

            return Optional.of(KiwoomAccountInfo.builder()
                    .userId(userId)
                    .kiwoomAccountId(account.getKiwoomAccountId())
                    .assignedAt(account.getAssignedAt())
                    .credentialsUpdatedAt(account.getCredentialsUpdatedAt())
                    .isActive(account.getIsActive())
                    .hasValidToken(tokenInfoOpt.isPresent())
                    .tokenExpiresAt(tokenInfoOpt.map(KiwoomTokenService.TokenInfo::getExpiresAt).orElse(null))
                    .build());

        } catch (Exception e) {
            log.error("Failed to get Kiwoom account info for user {}", userId, e);
            return Optional.empty();
        }
    }

    /**
     * 관리자용 전체 키움증권 계정 목록 조회
     */
    public List<KiwoomAccountView> getAllKiwoomAccounts() {
        try {
            log.debug("Getting all Kiwoom accounts for admin");
            return kiwoomAccountQueryService.getAllActiveAccounts();
        } catch (Exception e) {
            log.error("Failed to get all Kiwoom accounts", e);
            throw new KiwoomAccountManagementException("Failed to get all Kiwoom accounts", e);
        }
    }

    /**
     * 키움증권 계정 통계 조회
     */
    public KiwoomAccountStatistics getKiwoomAccountStatistics() {
        try {
            log.debug("Getting Kiwoom account statistics");

            var accountStats = kiwoomAccountQueryService.getAccountStatistics();
            var tokenStats = tokenService.getTokenStatistics();

            return KiwoomAccountStatistics.builder()
                    .totalAccounts(accountStats.getTotalAccounts())
                    .activeAccounts(accountStats.getActiveAccounts())
                    .inactiveAccounts(accountStats.getInactiveAccounts())
                    .accountsWithValidCredentials(accountStats.getAccountsWithValidCredentials())
                    .totalTokens(tokenStats.getTotalTokens())
                    .activeTokens(tokenStats.getActiveTokens())
                    .expiringTokens(tokenStats.getExpiringTokens())
                    .build();

        } catch (Exception e) {
            log.error("Failed to get Kiwoom account statistics", e);
            throw new KiwoomAccountManagementException("Failed to get statistics", e);
        }
    }

    // Private helper methods

    private void validateAssignmentInput(String userId, String kiwoomAccountId, String clientId, String clientSecret) {
        if (userId == null || userId.trim().isEmpty()) {
            throw new IllegalArgumentException("User ID cannot be null or empty");
        }
        if (kiwoomAccountId == null || kiwoomAccountId.trim().isEmpty()) {
            throw new IllegalArgumentException("Kiwoom account ID cannot be null or empty");
        }
        if (clientId == null || clientId.trim().isEmpty()) {
            throw new IllegalArgumentException("Client ID cannot be null or empty");
        }
        if (clientSecret == null || clientSecret.trim().isEmpty()) {
            throw new IllegalArgumentException("Client secret cannot be null or empty");
        }
    }

    private void validateAssignmentBusinessRules(String userId, String kiwoomAccountId) {
        // 1. 사용자가 이미 키움증권 계정을 가지고 있는지 확인
        if (kiwoomAccountQueryService.hasUserKiwoomAccount(userId)) {
            throw new KiwoomAccountManagementException("User already has a Kiwoom account assigned");
        }

        // 2. 키움증권 계정ID 중복 확인
        if (kiwoomAccountQueryService.isKiwoomAccountIdExists(kiwoomAccountId)) {
            throw new KiwoomAccountManagementException("Kiwoom account ID is already in use");
        }
    }

    private Optional<String> refreshKiwoomApiToken(String userId, KiwoomAccountView account) {
        try {
            log.info("Refreshing Kiwoom API token for user {}", userId);

            // 1. 암호화된 credentials 복호화
            EncryptedValue encryptedCredentials = EncryptedValue.of(
                    account.getEncryptedClientId(),
                    account.getEncryptionSalt()
            );
            ApiCredentials credentials = encryptionService.decryptApiCredentials(encryptedCredentials);

            // 2. 키움증권 API 호출하여 새 토큰 발급 (실제 구현 필요)
            // 여기서는 Mock 토큰 생성
            KiwoomTokenService.KiwoomToken newToken = KiwoomTokenService.KiwoomToken.builder()
                    .accessToken("mock_access_token_" + System.currentTimeMillis())
                    .tokenType("Bearer")
                    .expiresIn(14400L) // 4시간
                    .scope("trading")
                    .build();

            // 3. 새 토큰 저장
            tokenService.storeToken(userId, account.getKiwoomAccountId(), newToken);

            log.info("Successfully refreshed Kiwoom API token for user {}", userId);
            return Optional.of(newToken.getAccessToken());

        } catch (Exception e) {
            log.error("Failed to refresh Kiwoom API token for user {}", userId, e);
            return Optional.empty();
        }
    }

    // Inner classes for DTOs

    @lombok.Builder
    @lombok.Data
    public static class KiwoomAccountInfo {
        private String userId;
        private String kiwoomAccountId;
        private java.time.Instant assignedAt;
        private java.time.Instant credentialsUpdatedAt;
        private Boolean isActive;
        private Boolean hasValidToken;
        private java.time.Instant tokenExpiresAt;
    }

    @lombok.Builder
    @lombok.Data
    public static class KiwoomAccountStatistics {
        private long totalAccounts;
        private long activeAccounts;
        private long inactiveAccounts;
        private long accountsWithValidCredentials;
        private long totalTokens;
        private long activeTokens;
        private long expiringTokens;
    }

    /**
     * 키움증권 계정 관리 예외
     */
    public static class KiwoomAccountManagementException extends RuntimeException {
        public KiwoomAccountManagementException(String message) {
            super(message);
        }

        public KiwoomAccountManagementException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}