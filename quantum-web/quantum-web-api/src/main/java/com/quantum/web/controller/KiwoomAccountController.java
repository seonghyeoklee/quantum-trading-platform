package com.quantum.web.controller;

import com.quantum.trading.platform.query.view.KiwoomAccountView;
import com.quantum.web.security.UserPrincipal;
import com.quantum.web.service.KiwoomAccountManagementService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.Optional;

/**
 * 키움증권 계정 관리 REST API 컨트롤러
 *
 * 사용자별 키움증권 계정 관리 기능을 제공하는 REST API
 * - 계정 할당/취소/업데이트
 * - 토큰 관리 및 조회
 * - 계정 정보 조회
 */
@RestController
@RequestMapping("/api/v1/kiwoom-accounts")
@RequiredArgsConstructor
@Validated
@Slf4j
@Tag(name = "키움증권 계정 관리", description = "사용자별 키움증권 계정 관리 API")
public class KiwoomAccountController {

    private final KiwoomAccountManagementService kiwoomAccountManagementService;

    /**
     * 사용자가 직접 키움증권 계정 생성 및 API 키 등록
     */
    @PostMapping("/register")
    @Operation(summary = "키움증권 계정 등록", description = "사용자가 직접 키움증권 API 키를 등록합니다")
    public ResponseEntity<ApiResponse> registerKiwoomAccount(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Valid @RequestBody RegisterKiwoomAccountRequest request) {

        log.info("User {} registering Kiwoom account", userPrincipal.getId());

        try {
            // 키움증권 계정 ID 생성 (사용자별 유니크)
            String kiwoomAccountId = "KIWOOM_" + userPrincipal.getId() + "_" + System.currentTimeMillis();

            // 계정 할당 및 API 키 저장
            kiwoomAccountManagementService.assignKiwoomAccount(
                    userPrincipal.getId(),
                    kiwoomAccountId,
                    request.getClientId(),
                    request.getClientSecret()
            );

            return ResponseEntity.ok(ApiResponse.success(
                    "키움증권 계정이 성공적으로 등록되었습니다",
                    kiwoomAccountId
            ));

        } catch (Exception e) {
            log.error("Failed to register Kiwoom account for user {}", userPrincipal.getId(), e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("계정 등록에 실패했습니다: " + e.getMessage()));
        }
    }

    /**
     * 사용자의 키움증권 계정 정보 조회
     */
    @GetMapping("/me")
    public ResponseEntity<KiwoomAccountInfoResponse> getMyAccountInfo(
            @Parameter(hidden = true) @AuthenticationPrincipal UserPrincipal userPrincipal) {

        log.info("Getting Kiwoom account info for user: {}", userPrincipal.getId());

        Optional<KiwoomAccountManagementService.KiwoomAccountInfo> accountInfoOpt =
                kiwoomAccountManagementService.getUserKiwoomAccountInfo(userPrincipal.getId());

        if (accountInfoOpt.isEmpty()) {
            return ResponseEntity.ok(KiwoomAccountInfoResponse.noAccount());
        }

        KiwoomAccountManagementService.KiwoomAccountInfo accountInfo = accountInfoOpt.get();
        KiwoomAccountInfoResponse response = KiwoomAccountInfoResponse.builder()
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
     * 사용자의 키움증권 API 토큰 조회
     */
    @GetMapping("/me/token")
    public ResponseEntity<TokenResponse> getMyToken(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {

        log.info("Getting Kiwoom API token for user: {}", userPrincipal.getId());

        Optional<String> tokenOpt = kiwoomAccountManagementService.getKiwoomApiToken(userPrincipal.getId());

        if (tokenOpt.isEmpty()) {
            return ResponseEntity.ok(TokenResponse.builder()
                    .hasToken(false)
                    .message("No valid token available. Please check your Kiwoom account configuration.")
                    .build());
        }

        return ResponseEntity.ok(TokenResponse.builder()
                .hasToken(true)
                .accessToken(tokenOpt.get())
                .tokenType("Bearer")
                .message("Token retrieved successfully")
                .build());
    }

    /**
     * 사용자의 키움증권 인증 정보 업데이트
     */
    @PutMapping("/me/credentials")
    public ResponseEntity<ApiResponse> updateMyCredentials(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Valid @RequestBody UpdateCredentialsRequest request) {

        log.info("Updating Kiwoom credentials for user: {}", userPrincipal.getId());

        try {
            kiwoomAccountManagementService.updateKiwoomCredentials(
                    userPrincipal.getId(),
                    request.clientId,
                    request.clientSecret
            );

            return ResponseEntity.ok(ApiResponse.success("Credentials updated successfully"));

        } catch (KiwoomAccountManagementService.KiwoomAccountManagementException e) {
            log.warn("Failed to update credentials for user {}: {}", userPrincipal.getId(), e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error(e.getMessage()));
        }
    }

    /**
     * 사용자의 키움증권 계정 할당 취소 요청
     */
    @DeleteMapping("/me")
    public ResponseEntity<ApiResponse> revokeMyAccount(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Valid @RequestBody RevokeAccountRequest request) {

        log.info("User {} requesting account revocation, reason: {}",
                userPrincipal.getId(), request.reason);

        try {
            kiwoomAccountManagementService.revokeKiwoomAccount(
                    userPrincipal.getId(),
                    "User requested: " + request.reason
            );

            return ResponseEntity.ok(ApiResponse.success("Account revocation requested successfully"));

        } catch (KiwoomAccountManagementService.KiwoomAccountManagementException e) {
            log.warn("Failed to revoke account for user {}: {}", userPrincipal.getId(), e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error(e.getMessage()));
        }
    }

    // Request/Response DTOs

    @lombok.Data
    public static class RegisterKiwoomAccountRequest {
        @NotBlank(message = "Client ID(App Key)는 필수입니다")
        @Size(min = 10, max = 100, message = "Client ID는 10-100자 사이여야 합니다")
        private String clientId;

        @NotBlank(message = "Client Secret(App Secret)은 필수입니다")
        @Size(min = 20, max = 200, message = "Client Secret은 20-200자 사이여야 합니다")
        private String clientSecret;
    }

    @lombok.Data
    @lombok.Builder
    public static class KiwoomAccountInfoResponse {
        private boolean hasAccount;
        private String kiwoomAccountId;
        private java.time.Instant assignedAt;
        private java.time.Instant credentialsUpdatedAt;
        private Boolean isActive;
        private Boolean hasValidToken;
        private java.time.Instant tokenExpiresAt;
        private String userId;  // 추가

        public static KiwoomAccountInfoResponse noAccount() {
            return KiwoomAccountInfoResponse.builder()
                    .hasAccount(false)
                    .build();
        }
    }

    @lombok.Data
    @lombok.Builder
    public static class TokenResponse {
        private boolean hasToken;
        private String accessToken;
        private String tokenType;
        private String message;
    }

    @lombok.Data
    public static class UpdateCredentialsRequest {
        @NotBlank(message = "Client ID is required")
        @Size(min = 10, max = 100, message = "Client ID must be between 10 and 100 characters")
        private String clientId;

        @NotBlank(message = "Client secret is required")
        @Size(min = 20, max = 200, message = "Client secret must be between 20 and 200 characters")
        private String clientSecret;
    }

    @lombok.Data
    public static class RevokeAccountRequest {
        @NotBlank(message = "Reason is required")
        @Size(max = 500, message = "Reason must not exceed 500 characters")
        private String reason;
    }

    @lombok.Data
    @lombok.AllArgsConstructor
    @lombok.NoArgsConstructor
    public static class ApiResponse {
        private boolean success;
        private String message;
        private Object data;

        public static ApiResponse success(String message) {
            return new ApiResponse(true, message, null);
        }

        public static ApiResponse success(String message, Object data) {
            return new ApiResponse(true, message, data);
        }

        public static ApiResponse error(String message) {
            return new ApiResponse(false, message, null);
        }
    }
}
