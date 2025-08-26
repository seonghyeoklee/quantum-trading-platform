package com.quantum.web.controller;

import com.quantum.web.security.UserPrincipal;
import com.quantum.web.service.KiwoomTokenService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import java.time.Duration;
import java.util.Optional;

/**
 * 키움증권 토큰 관리 REST API 컨트롤러
 *
 * 키움증권 API 토큰의 직접적인 관리 기능을 제공하는 REST API
 * - 토큰 상태 조회
 * - 토큰 갱신 요청
 * - 토큰 무효화
 * - 토큰 TTL 관리
 */
@RestController
@RequestMapping("/api/v1/kiwoom-tokens")
@RequiredArgsConstructor
@Validated
@Slf4j
public class KiwoomTokenController {

    private final KiwoomTokenService kiwoomTokenService;

    /**
     * 사용자의 토큰 정보 조회
     */
    @GetMapping("/me")
    @PreAuthorize("hasRole('USER')")
    public ResponseEntity<TokenInfoResponse> getMyTokenInfo(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {

        log.info("Getting token info for user: {}", userPrincipal.getId());

        Optional<String> kiwoomAccountOpt = kiwoomTokenService.getUserKiwoomAccount(userPrincipal.getId());

        if (kiwoomAccountOpt.isEmpty()) {
            return ResponseEntity.ok(TokenInfoResponse.noAccount());
        }

        String kiwoomAccountId = kiwoomAccountOpt.get();
        Optional<KiwoomTokenService.TokenInfo> tokenInfoOpt =
                kiwoomTokenService.getTokenInfo(userPrincipal.getId(), kiwoomAccountId);

        if (tokenInfoOpt.isEmpty()) {
            return ResponseEntity.ok(TokenInfoResponse.noToken(kiwoomAccountId));
        }

        KiwoomTokenService.TokenInfo tokenInfo = tokenInfoOpt.get();
        boolean needsRefresh = kiwoomTokenService.needsRefresh(userPrincipal.getId(), kiwoomAccountId);

        return ResponseEntity.ok(TokenInfoResponse.builder()
                .hasToken(true)
                .kiwoomAccountId(kiwoomAccountId)
                .tokenType(tokenInfo.getTokenType())
                .issuedAt(tokenInfo.getIssuedAt())
                .expiresAt(tokenInfo.getExpiresAt())
                .needsRefresh(needsRefresh)
                .scope(tokenInfo.getScope())
                .build());
    }

    /**
     * 사용자의 토큰 갱신 필요 여부 확인
     */
    @GetMapping("/me/refresh-status")
    public ResponseEntity<RefreshStatusResponse> getMyRefreshStatus(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {

        log.info("Checking refresh status for user: {}", userPrincipal.getId());

        Optional<String> kiwoomAccountOpt = kiwoomTokenService.getUserKiwoomAccount(userPrincipal.getId());

        if (kiwoomAccountOpt.isEmpty()) {
            return ResponseEntity.ok(RefreshStatusResponse.builder()
                    .hasAccount(false)
                    .needsRefresh(false)
                    .message("No Kiwoom account found")
                    .build());
        }

        String kiwoomAccountId = kiwoomAccountOpt.get();
        boolean needsRefresh = kiwoomTokenService.needsRefresh(userPrincipal.getId(), kiwoomAccountId);

        return ResponseEntity.ok(RefreshStatusResponse.builder()
                .hasAccount(true)
                .kiwoomAccountId(kiwoomAccountId)
                .needsRefresh(needsRefresh)
                .message(needsRefresh ? "Token refresh is needed" : "Token is still valid")
                .build());
    }

    /**
     * 사용자의 토큰 무효화
     */
    @DeleteMapping("/me")
    public ResponseEntity<KiwoomAccountController.ApiResponse> invalidateMyToken(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {

        log.info("Invalidating token for user: {}", userPrincipal.getId());

        Optional<String> kiwoomAccountOpt = kiwoomTokenService.getUserKiwoomAccount(userPrincipal.getId());

        if (kiwoomAccountOpt.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error("No Kiwoom account found"));
        }

        try {
            kiwoomTokenService.invalidateToken(userPrincipal.getId(), kiwoomAccountOpt.get());
            return ResponseEntity.ok(KiwoomAccountController.ApiResponse.success("Token invalidated successfully"));

        } catch (KiwoomTokenService.TokenManagementException e) {
            log.warn("Failed to invalidate token for user {}: {}", userPrincipal.getId(), e.getMessage());
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error(e.getMessage()));
        }
    }

    /**
     * 사용자의 토큰 TTL 연장 요청
     */
    @PostMapping("/me/extend-ttl")
    public ResponseEntity<KiwoomAccountController.ApiResponse> extendMyTokenTTL(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Valid @RequestBody ExtendTTLRequest request) {

        log.info("Extending token TTL for user: {} by {} hours",
                userPrincipal.getId(), request.extensionHours);

        Optional<String> kiwoomAccountOpt = kiwoomTokenService.getUserKiwoomAccount(userPrincipal.getId());

        if (kiwoomAccountOpt.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error("No Kiwoom account found"));
        }

        try {
            Duration extensionTime = Duration.ofHours(request.extensionHours);
            kiwoomTokenService.extendTokenTTL(userPrincipal.getId(), kiwoomAccountOpt.get(), extensionTime);

            return ResponseEntity.ok(KiwoomAccountController.ApiResponse.success(
                    String.format("Token TTL extended by %d hours", request.extensionHours)
            ));

        } catch (Exception e) {
            log.warn("Failed to extend token TTL for user {}: {}", userPrincipal.getId(), e.getMessage());
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error("Failed to extend token TTL: " + e.getMessage()));
        }
    }

    // 관리자용 API

    /**
     * 토큰 통계 조회 (관리자용)
     */
    @GetMapping("/statistics")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<KiwoomTokenService.TokenStatistics> getTokenStatistics() {
        log.info("Admin requesting token statistics");

        KiwoomTokenService.TokenStatistics statistics = kiwoomTokenService.getTokenStatistics();
        return ResponseEntity.ok(statistics);
    }

    /**
     * 특정 사용자의 토큰 정보 조회 (관리자용)
     */
    @GetMapping("/users/{userId}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<AdminTokenInfoResponse> getUserTokenInfo(
            @PathVariable @NotBlank String userId) {

        log.info("Admin requesting token info for user: {}", userId);

        Optional<String> kiwoomAccountOpt = kiwoomTokenService.getUserKiwoomAccount(userId);

        if (kiwoomAccountOpt.isEmpty()) {
            return ResponseEntity.ok(AdminTokenInfoResponse.noAccount(userId));
        }

        String kiwoomAccountId = kiwoomAccountOpt.get();
        Optional<KiwoomTokenService.TokenInfo> tokenInfoOpt =
                kiwoomTokenService.getTokenInfo(userId, kiwoomAccountId);

        if (tokenInfoOpt.isEmpty()) {
            return ResponseEntity.ok(AdminTokenInfoResponse.noToken(userId, kiwoomAccountId));
        }

        KiwoomTokenService.TokenInfo tokenInfo = tokenInfoOpt.get();
        boolean needsRefresh = kiwoomTokenService.needsRefresh(userId, kiwoomAccountId);

        return ResponseEntity.ok(AdminTokenInfoResponse.builder()
                .userId(userId)
                .hasToken(true)
                .kiwoomAccountId(kiwoomAccountId)
                .tokenType(tokenInfo.getTokenType())
                .issuedAt(tokenInfo.getIssuedAt())
                .expiresAt(tokenInfo.getExpiresAt())
                .needsRefresh(needsRefresh)
                .scope(tokenInfo.getScope())
                .build());
    }

    /**
     * 특정 사용자의 토큰 무효화 (관리자용)
     */
    @DeleteMapping("/users/{userId}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<KiwoomAccountController.ApiResponse> invalidateUserToken(
            @PathVariable @NotBlank String userId) {

        log.info("Admin invalidating token for user: {}", userId);

        Optional<String> kiwoomAccountOpt = kiwoomTokenService.getUserKiwoomAccount(userId);

        if (kiwoomAccountOpt.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error("No Kiwoom account found for user"));
        }

        try {
            kiwoomTokenService.invalidateToken(userId, kiwoomAccountOpt.get());
            return ResponseEntity.ok(KiwoomAccountController.ApiResponse.success(
                    String.format("Token invalidated successfully for user %s", userId)
            ));

        } catch (KiwoomTokenService.TokenManagementException e) {
            log.warn("Failed to invalidate token for user {}: {}", userId, e.getMessage());
            return ResponseEntity.badRequest()
                    .body(KiwoomAccountController.ApiResponse.error(e.getMessage()));
        }
    }

    // Request/Response DTOs

    @lombok.Data
    @lombok.Builder
    public static class TokenInfoResponse {
        private boolean hasToken;
        private String kiwoomAccountId;
        private String tokenType;
        private java.time.Instant issuedAt;
        private java.time.Instant expiresAt;
        private boolean needsRefresh;
        private String scope;

        public static TokenInfoResponse noAccount() {
            return TokenInfoResponse.builder()
                    .hasToken(false)
                    .build();
        }

        public static TokenInfoResponse noToken(String kiwoomAccountId) {
            return TokenInfoResponse.builder()
                    .hasToken(false)
                    .kiwoomAccountId(kiwoomAccountId)
                    .build();
        }
    }

    @lombok.Data
    @lombok.Builder
    public static class AdminTokenInfoResponse {
        private String userId;
        private boolean hasToken;
        private String kiwoomAccountId;
        private String tokenType;
        private java.time.Instant issuedAt;
        private java.time.Instant expiresAt;
        private boolean needsRefresh;
        private String scope;

        public static AdminTokenInfoResponse noAccount(String userId) {
            return AdminTokenInfoResponse.builder()
                    .userId(userId)
                    .hasToken(false)
                    .build();
        }

        public static AdminTokenInfoResponse noToken(String userId, String kiwoomAccountId) {
            return AdminTokenInfoResponse.builder()
                    .userId(userId)
                    .hasToken(false)
                    .kiwoomAccountId(kiwoomAccountId)
                    .build();
        }
    }

    @lombok.Data
    @lombok.Builder
    public static class RefreshStatusResponse {
        private boolean hasAccount;
        private String kiwoomAccountId;
        private boolean needsRefresh;
        private String message;
    }

    @lombok.Data
    public static class ExtendTTLRequest {
        @Positive(message = "Extension hours must be positive")
        private int extensionHours = 1;
    }
}
