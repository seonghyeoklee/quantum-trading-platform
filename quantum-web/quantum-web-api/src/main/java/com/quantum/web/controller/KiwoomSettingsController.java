package com.quantum.web.controller;

import com.quantum.trading.platform.query.view.UserKiwoomSettingsView;
import com.quantum.web.dto.ApiResponse;
import com.quantum.web.service.UserKiwoomSettingsService;
import com.quantum.web.service.UserKiwoomSettingsService.UserSettingsUpdateRequest;
import com.quantum.web.service.UserKiwoomSettingsService.UserSettingsStatistics;
import com.quantum.web.security.UserPrincipal;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;

/**
 * 키움증권 사용자 설정 관리 컨트롤러
 *
 * 사용자별 키움증권 거래 모드 설정, 토큰 관리 설정 등을 관리
 */
@RestController
@RequestMapping("/api/v1/kiwoom/settings")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Kiwoom Settings", description = "키움증권 사용자 설정 관리 API")
@SecurityRequirement(name = "bearerAuth")
public class KiwoomSettingsController {

    private final UserKiwoomSettingsService userKiwoomSettingsService;

    /**
     * 현재 사용자의 키움 설정 조회
     */
    @GetMapping
    @Operation(summary = "키움 설정 조회", description = "현재 사용자의 키움증권 설정 정보를 조회합니다")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<ApiResponse<UserKiwoomSettingsView>> getUserSettings(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            log.info("Getting Kiwoom settings for user: {}", userPrincipal.getUsername());

            UserKiwoomSettingsView settings = userKiwoomSettingsService.getUserSettings(userPrincipal.getId());

            return ResponseEntity.ok(ApiResponse.success(settings, "키움 설정 조회 성공"));

        } catch (Exception e) {
            log.error("Failed to get Kiwoom settings for user: {}", userPrincipal.getUsername(), e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("키움 설정 조회 실패: " + e.getMessage()));
        }
    }

    /**
     * 거래 모드 전환 (sandbox ↔ real)
     */
    @PostMapping("/switch-mode")
    @Operation(summary = "거래 모드 전환", description = "사용자의 기본 거래 모드를 sandbox/real 간에 전환합니다")
    @ApiResponses({
        @io.swagger.v3.oas.annotations.responses.ApiResponse(responseCode = "200", description = "모드 전환 성공"),
        @io.swagger.v3.oas.annotations.responses.ApiResponse(responseCode = "400", description = "모드 전환 실패")
    })
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<ApiResponse<UserKiwoomSettingsView>> switchTradingMode(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Parameter(description = "새로운 거래 모드 (true: 실전투자, false: 모의투자)")
            @RequestParam boolean realMode) {
        try {
            log.info("Switching trading mode for user {} to {}",
                    userPrincipal.getUsername(), realMode ? "real" : "sandbox");

            UserKiwoomSettingsView settings = userKiwoomSettingsService.switchTradingMode(
                    userPrincipal.getId(), realMode);

            String modeDescription = realMode ? "실전투자" : "모의투자";
            return ResponseEntity.ok(ApiResponse.success(settings,
                    String.format("거래 모드를 %s로 전환하였습니다", modeDescription)));

        } catch (Exception e) {
            log.error("Failed to switch trading mode for user: {}", userPrincipal.getUsername(), e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("거래 모드 전환 실패: " + e.getMessage()));
        }
    }

    /**
     * 토큰 만료 알림 설정 업데이트
     */
    @PostMapping("/token-notification")
    @Operation(summary = "토큰 만료 알림 설정", description = "토큰 만료 알림 활성화 여부와 임계시간을 설정합니다")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<ApiResponse<UserKiwoomSettingsView>> updateTokenNotification(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Parameter(description = "알림 활성화 여부")
            @RequestParam boolean enabled,
            @Parameter(description = "알림 임계시간 (분)", example = "30")
            @RequestParam(required = false) Integer thresholdMinutes) {
        try {
            log.info("Updating token notification for user {}: enabled={}, threshold={}min",
                    userPrincipal.getUsername(), enabled, thresholdMinutes);

            UserKiwoomSettingsView settings = userKiwoomSettingsService.updateTokenExpiryNotification(
                    userPrincipal.getId(), enabled, thresholdMinutes);

            return ResponseEntity.ok(ApiResponse.success(settings, "토큰 만료 알림 설정이 업데이트되었습니다"));

        } catch (Exception e) {
            log.error("Failed to update token notification for user: {}", userPrincipal.getUsername(), e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("토큰 알림 설정 실패: " + e.getMessage()));
        }
    }

    /**
     * 자동 토큰 갱신 설정
     */
    @PostMapping("/auto-refresh")
    @Operation(summary = "자동 토큰 갱신 설정", description = "토큰 자동 갱신 기능을 활성화/비활성화합니다")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<ApiResponse<UserKiwoomSettingsView>> updateAutoRefresh(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Parameter(description = "자동 갱신 활성화 여부")
            @RequestParam boolean enabled) {
        try {
            log.info("Updating auto refresh for user {}: enabled={}",
                    userPrincipal.getUsername(), enabled);

            UserKiwoomSettingsView settings = userKiwoomSettingsService.updateAutoRefreshSetting(
                    userPrincipal.getId(), enabled);

            return ResponseEntity.ok(ApiResponse.success(settings, "자동 토큰 갱신 설정이 업데이트되었습니다"));

        } catch (Exception e) {
            log.error("Failed to update auto refresh for user: {}", userPrincipal.getUsername(), e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("자동 갱신 설정 실패: " + e.getMessage()));
        }
    }

    /**
     * 모드 전환 시 자동 재발급 설정
     */
    @PostMapping("/auto-reissue")
    @Operation(summary = "자동 토큰 재발급 설정", description = "모드 전환 시 토큰 자동 재발급 기능을 설정합니다")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<ApiResponse<UserKiwoomSettingsView>> updateAutoReissue(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Parameter(description = "자동 재발급 활성화 여부")
            @RequestParam boolean enabled) {
        try {
            log.info("Updating auto reissue for user {}: enabled={}",
                    userPrincipal.getUsername(), enabled);

            UserKiwoomSettingsView settings = userKiwoomSettingsService.updateAutoReissueSetting(
                    userPrincipal.getId(), enabled);

            return ResponseEntity.ok(ApiResponse.success(settings, "자동 재발급 설정이 업데이트되었습니다"));

        } catch (Exception e) {
            log.error("Failed to update auto reissue for user: {}", userPrincipal.getUsername(), e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("자동 재발급 설정 실패: " + e.getMessage()));
        }
    }

    /**
     * 전체 설정 업데이트
     */
    @PutMapping
    @Operation(summary = "전체 설정 업데이트", description = "키움증권 설정을 일괄 업데이트합니다")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<ApiResponse<UserKiwoomSettingsView>> updateAllSettings(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Valid @RequestBody UserSettingsUpdateRequest request) {
        try {
            log.info("Updating all settings for user {}: {}",
                    userPrincipal.getUsername(), request);

            UserKiwoomSettingsView settings = userKiwoomSettingsService.updateUserSettings(
                    userPrincipal.getId(), request);

            return ResponseEntity.ok(ApiResponse.success(settings, "키움 설정이 업데이트되었습니다"));

        } catch (Exception e) {
            log.error("Failed to update settings for user: {}", userPrincipal.getUsername(), e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("설정 업데이트 실패: " + e.getMessage()));
        }
    }

    /**
     * 현재 거래 모드 조회
     */
    @GetMapping("/current-mode")
    @Operation(summary = "현재 거래 모드 조회", description = "사용자의 현재 기본 거래 모드를 조회합니다")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getCurrentMode(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            log.debug("Getting current trading mode for user: {}", userPrincipal.getUsername());

            boolean isRealMode = userKiwoomSettingsService.getUserDefaultRealMode(userPrincipal.getId());

            Map<String, Object> result = Map.of(
                    "userId", userPrincipal.getId(),
                    "username", userPrincipal.getUsername(),
                    "isRealMode", isRealMode,
                    "modeDescription", isRealMode ? "실전투자" : "모의투자"
            );

            return ResponseEntity.ok(ApiResponse.success(result, "현재 거래 모드 조회 성공"));

        } catch (Exception e) {
            log.error("Failed to get current mode for user: {}", userPrincipal.getUsername(), e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("거래 모드 조회 실패: " + e.getMessage()));
        }
    }

    // ===== 관리자용 API =====

    /**
     * 전체 사용자 설정 통계 (관리자용)
     */
    @GetMapping("/admin/statistics")
    @Operation(summary = "키움 설정 통계", description = "전체 사용자의 키움 설정 통계를 조회합니다 (관리자 전용)")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<UserSettingsStatistics>> getSettingsStatistics(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            log.info("Admin {} requesting settings statistics", userPrincipal.getUsername());

            UserSettingsStatistics statistics = userKiwoomSettingsService.getUserSettingsStatistics();

            return ResponseEntity.ok(ApiResponse.success(statistics, "설정 통계 조회 성공"));

        } catch (Exception e) {
            log.error("Failed to get settings statistics", e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("통계 조회 실패: " + e.getMessage()));
        }
    }

    /**
     * 최근 모드 변경 내역 (관리자용)
     */
    @GetMapping("/admin/recent-changes")
    @Operation(summary = "최근 모드 변경 내역", description = "최근 거래 모드를 변경한 사용자 목록을 조회합니다 (관리자 전용)")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<List<UserKiwoomSettingsView>>> getRecentModeChanges(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Parameter(description = "조회 시간 범위 (시간)", example = "24")
            @RequestParam(defaultValue = "24") int hours) {
        try {
            log.info("Admin {} requesting recent mode changes for {} hours",
                    userPrincipal.getUsername(), hours);

            List<UserKiwoomSettingsView> recentChanges = userKiwoomSettingsService.getRecentModeChanges(hours);

            return ResponseEntity.ok(ApiResponse.success(recentChanges,
                    String.format("최근 %d시간 모드 변경 내역 조회 성공", hours)));

        } catch (Exception e) {
            log.error("Failed to get recent mode changes", e);
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("모드 변경 내역 조회 실패: " + e.getMessage()));
        }
    }
}
