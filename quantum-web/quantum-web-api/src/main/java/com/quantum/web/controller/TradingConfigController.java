package com.quantum.web.controller;

import com.quantum.web.dto.ApiResponse;
import com.quantum.web.dto.TradingConfigDto;
import com.quantum.web.security.UserPrincipal;
import com.quantum.web.service.TradingConfigService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.List;

/**
 * 트레이딩 설정 컨트롤러
 */
@RestController
@RequestMapping("/api/v1/trading/config")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Trading Configuration", description = "트레이딩 설정 관리 API")
@SecurityRequirement(name = "Bearer Authentication")
public class TradingConfigController {

    private final TradingConfigService tradingConfigService;

    /**
     * 현재 사용자의 트레이딩 설정 조회
     */
    @GetMapping("/settings")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    @Operation(summary = "트레이딩 설정 조회", description = "현재 로그인한 사용자의 트레이딩 설정을 조회합니다")
    public ResponseEntity<ApiResponse<TradingConfigDto.UserTradingSettingsResponse>> getTradingSettings(
            @AuthenticationPrincipal UserPrincipal currentUser) {

        log.info("트레이딩 설정 조회 요청: userId={}", currentUser.getUsername());

        try {
            TradingConfigDto.UserTradingSettingsResponse settings =
                tradingConfigService.getUserTradingSettings(currentUser.getUsername());

            return ResponseEntity.ok(ApiResponse.success(settings, "트레이딩 설정 조회 성공"));

        } catch (Exception e) {
            log.error("트레이딩 설정 조회 실패: userId={}, error={}", currentUser.getUsername(), e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("트레이딩 설정 조회에 실패했습니다: " + e.getMessage()));
        }
    }

    /**
     * 트레이딩 설정 업데이트
     */
    @PutMapping("/settings")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    @Operation(summary = "트레이딩 설정 업데이트", description = "현재 사용자의 트레이딩 설정을 업데이트합니다")
    public ResponseEntity<ApiResponse<TradingConfigDto.UserTradingSettingsResponse>> updateTradingSettings(
            @Valid @RequestBody TradingConfigDto.UserTradingSettingsUpdateRequest request,
            @AuthenticationPrincipal UserPrincipal currentUser,
            HttpServletRequest httpRequest) {

        log.info("트레이딩 설정 업데이트 요청: userId={}, tradingMode={}",
                currentUser.getUsername(), request.getTradingMode());

        try {
            TradingConfigDto.UserTradingSettingsResponse updatedSettings =
                tradingConfigService.updateUserTradingSettings(
                    currentUser.getUsername(), request, currentUser, httpRequest);

            return ResponseEntity.ok(ApiResponse.success(updatedSettings, "트레이딩 설정 업데이트 성공"));

        } catch (IllegalArgumentException e) {
            log.warn("트레이딩 설정 업데이트 실패 (유효성 검사): userId={}, error={}",
                    currentUser.getUsername(), e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error(e.getMessage()));

        } catch (Exception e) {
            log.error("트레이딩 설정 업데이트 실패: userId={}, error={}",
                    currentUser.getUsername(), e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("트레이딩 설정 업데이트에 실패했습니다: " + e.getMessage()));
        }
    }

    /**
     * 트레이딩 모드만 변경
     */
    @PostMapping("/mode")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    @Operation(summary = "트레이딩 모드 변경", description = "트레이딩 모드를 모의투자/실전투자로 변경합니다")
    public ResponseEntity<ApiResponse<TradingConfigDto.UserTradingSettingsResponse>> changeTradingMode(
            @Valid @RequestBody TradingConfigDto.TradingModeChangeRequest request,
            @AuthenticationPrincipal UserPrincipal currentUser,
            HttpServletRequest httpRequest) {

        log.info("트레이딩 모드 변경 요청: userId={}, newMode={}",
                currentUser.getUsername(), request.getTradingMode());

        try {
            TradingConfigDto.UserTradingSettingsResponse updatedSettings =
                tradingConfigService.changeTradingMode(
                    currentUser.getUsername(), request, currentUser, httpRequest);

            return ResponseEntity.ok(ApiResponse.success(updatedSettings,
                    String.format("트레이딩 모드가 %s(으)로 변경되었습니다",
                            request.getTradingMode().getDescription())));

        } catch (IllegalArgumentException e) {
            log.warn("트레이딩 모드 변경 실패 (유효성 검사): userId={}, error={}",
                    currentUser.getUsername(), e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error(e.getMessage()));

        } catch (Exception e) {
            log.error("트레이딩 모드 변경 실패: userId={}, error={}",
                    currentUser.getUsername(), e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("트레이딩 모드 변경에 실패했습니다: " + e.getMessage()));
        }
    }

    /**
     * 트레이딩 모드 변경 이력 조회
     */
    @GetMapping("/mode/history")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    @Operation(summary = "모드 변경 이력 조회", description = "현재 사용자의 트레이딩 모드 변경 이력을 조회합니다")
    public ResponseEntity<ApiResponse<List<TradingConfigDto.TradingModeHistoryResponse>>> getModeHistory(
            @AuthenticationPrincipal UserPrincipal currentUser) {

        log.info("모드 변경 이력 조회 요청: userId={}", currentUser.getUsername());

        try {
            List<TradingConfigDto.TradingModeHistoryResponse> history =
                tradingConfigService.getUserModeHistory(currentUser.getUsername());

            return ResponseEntity.ok(ApiResponse.success(history, "모드 변경 이력 조회 성공"));

        } catch (Exception e) {
            log.error("모드 변경 이력 조회 실패: userId={}, error={}",
                    currentUser.getUsername(), e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("모드 변경 이력 조회에 실패했습니다: " + e.getMessage()));
        }
    }

    /**
     * 트레이딩 설정 요약 정보 조회
     */
    @GetMapping("/summary")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    @Operation(summary = "트레이딩 설정 요약", description = "대시보드에 표시할 트레이딩 설정 요약 정보를 조회합니다")
    public ResponseEntity<ApiResponse<TradingConfigDto.TradingConfigSummaryResponse>> getTradingConfigSummary(
            @AuthenticationPrincipal UserPrincipal currentUser) {

        log.info("트레이딩 설정 요약 조회 요청: userId={}", currentUser.getUsername());

        try {
            TradingConfigDto.TradingConfigSummaryResponse summary =
                tradingConfigService.getTradingConfigSummary(currentUser.getUsername());

            return ResponseEntity.ok(ApiResponse.success(summary, "트레이딩 설정 요약 조회 성공"));

        } catch (Exception e) {
            log.error("트레이딩 설정 요약 조회 실패: userId={}, error={}",
                    currentUser.getUsername(), e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("트레이딩 설정 요약 조회에 실패했습니다: " + e.getMessage()));
        }
    }

    /**
     * 관리자용: 특정 사용자 트레이딩 설정 조회
     */
    @GetMapping("/admin/settings/{userId}")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "[관리자] 사용자 트레이딩 설정 조회", description = "관리자가 특정 사용자의 트레이딩 설정을 조회합니다")
    public ResponseEntity<ApiResponse<TradingConfigDto.UserTradingSettingsResponse>> getUserTradingSettings(
            @Parameter(description = "조회할 사용자 ID") @PathVariable String userId,
            @AuthenticationPrincipal UserPrincipal currentUser) {

        log.info("관리자 트레이딩 설정 조회 요청: adminId={}, targetUserId={}",
                currentUser.getUsername(), userId);

        try {
            TradingConfigDto.UserTradingSettingsResponse settings =
                tradingConfigService.getUserTradingSettings(userId);

            return ResponseEntity.ok(ApiResponse.success(settings, "사용자 트레이딩 설정 조회 성공"));

        } catch (Exception e) {
            log.error("관리자 트레이딩 설정 조회 실패: adminId={}, targetUserId={}, error={}",
                    currentUser.getUsername(), userId, e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("사용자 트레이딩 설정 조회에 실패했습니다: " + e.getMessage()));
        }
    }

    /**
     * 관리자용: 특정 사용자 트레이딩 모드 강제 변경
     */
    @PostMapping("/admin/mode/{userId}")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "[관리자] 사용자 트레이딩 모드 강제 변경",
               description = "관리자가 특정 사용자의 트레이딩 모드를 강제로 변경합니다")
    public ResponseEntity<ApiResponse<TradingConfigDto.UserTradingSettingsResponse>> adminChangeTradingMode(
            @Parameter(description = "대상 사용자 ID") @PathVariable String userId,
            @Valid @RequestBody TradingConfigDto.TradingModeChangeRequest request,
            @AuthenticationPrincipal UserPrincipal currentUser,
            HttpServletRequest httpRequest) {

        log.info("관리자 트레이딩 모드 변경 요청: adminId={}, targetUserId={}, newMode={}",
                currentUser.getUsername(), userId, request.getTradingMode());

        try {
            TradingConfigDto.UserTradingSettingsResponse updatedSettings =
                tradingConfigService.changeTradingMode(userId, request, currentUser, httpRequest);

            return ResponseEntity.ok(ApiResponse.success(updatedSettings,
                String.format("사용자 %s의 트레이딩 모드가 %s(으)로 변경되었습니다",
                            userId, request.getTradingMode().getDescription())));

        } catch (IllegalArgumentException e) {
            log.warn("관리자 트레이딩 모드 변경 실패 (유효성 검사): adminId={}, targetUserId={}, error={}",
                    currentUser.getUsername(), userId, e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error(e.getMessage()));

        } catch (Exception e) {
            log.error("관리자 트레이딩 모드 변경 실패: adminId={}, targetUserId={}, error={}",
                    currentUser.getUsername(), userId, e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("트레이딩 모드 변경에 실패했습니다: " + e.getMessage()));
        }
    }
}
