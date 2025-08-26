package com.quantum.web.controller;

import com.quantum.trading.platform.query.view.KiwoomAccountView;
import com.quantum.web.service.KiwoomAccountManagementService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.Optional;

/**
 * 관리자용 키움증권 계정 관리 REST API 컨트롤러
 * 
 * 관리자가 모든 사용자의 키움증권 계정을 관리할 수 있는 REST API
 * - 전체 계정 조회 및 통계
 * - 사용자별 계정 할당/취소/업데이트
 * - 시스템 관리 기능
 */
@RestController
@RequestMapping("/api/v1/admin/kiwoom-accounts")
@RequiredArgsConstructor
@Validated
@Slf4j
@PreAuthorize("hasRole('ADMIN')")
public class AdminKiwoomAccountController {

    private final KiwoomAccountManagementService kiwoomAccountManagementService;

    /**
     * 모든 키움증권 계정 목록 조회
     */
    @GetMapping
    public ResponseEntity<List<KiwoomAccountView>> getAllAccounts() {
        log.info("Admin requesting all Kiwoom accounts");
        
        List<KiwoomAccountView> accounts = kiwoomAccountManagementService.getAllKiwoomAccounts();
        return ResponseEntity.ok(accounts);
    }

    /**
     * 키움증권 계정 통계 조회
     */
    @GetMapping("/statistics")
    public ResponseEntity<KiwoomAccountManagementService.KiwoomAccountStatistics> getAccountStatistics() {
        log.info("Admin requesting Kiwoom account statistics");
        
        KiwoomAccountManagementService.KiwoomAccountStatistics statistics = 
                kiwoomAccountManagementService.getKiwoomAccountStatistics();
        return ResponseEntity.ok(statistics);
    }

    /**
     * 특정 사용자의 키움증권 계정 정보 조회
     */
    @GetMapping("/users/{userId}")
    public ResponseEntity<AdminAccountInfoResponse> getUserAccountInfo(
            @PathVariable @NotBlank String userId) {
        
        log.info("Admin requesting account info for user: {}", userId);
        
        Optional<KiwoomAccountManagementService.KiwoomAccountInfo> accountInfoOpt = 
                kiwoomAccountManagementService.getUserKiwoomAccountInfo(userId);
        
        if (accountInfoOpt.isEmpty()) {
            return ResponseEntity.ok(AdminAccountInfoResponse.noAccount(userId));
        }
        
        KiwoomAccountManagementService.KiwoomAccountInfo accountInfo = accountInfoOpt.get();
        AdminAccountInfoResponse response = AdminAccountInfoResponse.builder()
                .userId(userId)
                .hasAccount(true)
                .kiwoomAccountId(accountInfo.getKiwoomAccountId())
                .assignedAt(accountInfo.getAssignedAt())
                .credentialsUpdatedAt(accountInfo.getCredentialsUpdatedAt())
                .isActive(accountInfo.getIsActive())
                .hasValidToken(accountInfo.getHasValidToken())
                .tokenExpiresAt(accountInfo.getTokenExpiresAt())
                .build();
        
        return ResponseEntity.ok(response);
    }

    /**
     * 사용자에게 키움증권 계정 할당
     */
    @PostMapping("/users/{userId}/assign")
    public ResponseEntity<KiwoomAccountController.ApiResponse> assignAccountToUser(
            @PathVariable @NotBlank String userId,
            @Valid @RequestBody AssignAccountRequest request) {
        
        log.info("Admin assigning Kiwoom account {} to user {}", 
                request.kiwoomAccountId, userId);
        
        try {
            kiwoomAccountManagementService.assignKiwoomAccount(
                    userId,
                    request.kiwoomAccountId,
                    request.clientId,
                    request.clientSecret
            );
            
            return ResponseEntity.ok(KiwoomAccountController.ApiResponse.success(
                    String.format("Successfully assigned Kiwoom account %s to user %s", 
                            request.kiwoomAccountId, userId)
            ));
            
        } catch (KiwoomAccountManagementService.KiwoomAccountManagementException e) {
            log.warn("Failed to assign account for user {}: {}", userId, e.getMessage());
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error(e.getMessage()));
        } catch (IllegalArgumentException e) {
            log.warn("Invalid input for account assignment: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error("Invalid input: " + e.getMessage()));
        }
    }

    /**
     * 사용자의 키움증권 인증 정보 업데이트 (관리자용)
     */
    @PutMapping("/users/{userId}/credentials")
    public ResponseEntity<KiwoomAccountController.ApiResponse> updateUserCredentials(
            @PathVariable @NotBlank String userId,
            @Valid @RequestBody KiwoomAccountController.UpdateCredentialsRequest request) {
        
        log.info("Admin updating Kiwoom credentials for user: {}", userId);
        
        try {
            kiwoomAccountManagementService.updateKiwoomCredentials(
                    userId,
                    request.getClientId(),
                    request.getClientSecret()
            );
            
            return ResponseEntity.ok(KiwoomAccountController.ApiResponse.success(
                    String.format("Successfully updated credentials for user %s", userId)
            ));
            
        } catch (KiwoomAccountManagementService.KiwoomAccountManagementException e) {
            log.warn("Failed to update credentials for user {}: {}", userId, e.getMessage());
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error(e.getMessage()));
        }
    }

    /**
     * 사용자의 키움증권 계정 할당 취소 (관리자용)
     */
    @DeleteMapping("/users/{userId}")
    public ResponseEntity<KiwoomAccountController.ApiResponse> revokeUserAccount(
            @PathVariable @NotBlank String userId,
            @Valid @RequestBody AdminRevokeAccountRequest request) {
        
        log.info("Admin revoking Kiwoom account for user {}, reason: {}", 
                userId, request.reason);
        
        try {
            kiwoomAccountManagementService.revokeKiwoomAccount(
                    userId,
                    "Admin action: " + request.reason
            );
            
            return ResponseEntity.ok(KiwoomAccountController.ApiResponse.success(
                    String.format("Successfully revoked Kiwoom account for user %s", userId)
            ));
            
        } catch (KiwoomAccountManagementService.KiwoomAccountManagementException e) {
            log.warn("Failed to revoke account for user {}: {}", userId, e.getMessage());
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error(e.getMessage()));
        }
    }

    /**
     * 특정 사용자의 키움증권 API 토큰 조회 (관리자용)
     */
    @GetMapping("/users/{userId}/token")
    public ResponseEntity<AdminTokenResponse> getUserToken(
            @PathVariable @NotBlank String userId) {
        
        log.info("Admin requesting Kiwoom API token for user: {}", userId);
        
        Optional<String> tokenOpt = kiwoomAccountManagementService.getKiwoomApiToken(userId);
        
        if (tokenOpt.isEmpty()) {
            return ResponseEntity.ok(AdminTokenResponse.builder()
                    .userId(userId)
                    .hasToken(false)
                    .message("No valid token available for this user")
                    .build());
        }
        
        return ResponseEntity.ok(AdminTokenResponse.builder()
                .userId(userId)
                .hasToken(true)
                .accessToken(tokenOpt.get())
                .tokenType("Bearer")
                .message("Token retrieved successfully")
                .build());
    }

    /**
     * 시스템 전체 토큰 갱신 트리거 (관리자용)
     */
    @PostMapping("/tokens/refresh")
    public ResponseEntity<KiwoomAccountController.ApiResponse> triggerTokenRefresh() {
        log.info("Admin triggering system-wide token refresh");
        
        // 이 기능은 향후 구현할 수 있습니다 (예: 모든 만료 임박 토큰 갱신)
        return ResponseEntity.ok(KiwoomAccountController.ApiResponse.success(
                "Token refresh trigger initiated (feature to be implemented)"
        ));
    }

    // Request/Response DTOs

    @lombok.Data
    @lombok.Builder
    public static class AdminAccountInfoResponse {
        private String userId;
        private boolean hasAccount;
        private String kiwoomAccountId;
        private java.time.Instant assignedAt;
        private java.time.Instant credentialsUpdatedAt;
        private Boolean isActive;
        private Boolean hasValidToken;
        private java.time.Instant tokenExpiresAt;
        
        public static AdminAccountInfoResponse noAccount(String userId) {
            return AdminAccountInfoResponse.builder()
                    .userId(userId)
                    .hasAccount(false)
                    .build();
        }
    }

    @lombok.Data
    @lombok.Builder
    public static class AdminTokenResponse {
        private String userId;
        private boolean hasToken;
        private String accessToken;
        private String tokenType;
        private String message;
    }

    @lombok.Data
    public static class AssignAccountRequest {
        @NotBlank(message = "Kiwoom account ID is required")
        @Size(min = 5, max = 50, message = "Kiwoom account ID must be between 5 and 50 characters")
        private String kiwoomAccountId;

        @NotBlank(message = "Client ID is required")
        @Size(min = 10, max = 100, message = "Client ID must be between 10 and 100 characters")
        private String clientId;

        @NotBlank(message = "Client secret is required")
        @Size(min = 20, max = 200, message = "Client secret must be between 20 and 200 characters")
        private String clientSecret;
    }

    @lombok.Data
    public static class AdminRevokeAccountRequest {
        @NotBlank(message = "Reason is required")
        @Size(max = 500, message = "Reason must not exceed 500 characters")
        private String reason;
        
        private boolean forceRevoke = false; // 강제 취소 여부
    }
}