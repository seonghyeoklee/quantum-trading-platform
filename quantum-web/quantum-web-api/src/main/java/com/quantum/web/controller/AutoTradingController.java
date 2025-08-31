package com.quantum.web.controller;

import com.quantum.web.dto.ApiResponse;
import com.quantum.web.dto.AutoTradingConfigDto;
import com.quantum.web.dto.AutoTradingStatusDto;
import com.quantum.web.service.AutoTradingService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Max;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;

/**
 * 자동매매 설정 및 관리 컨트롤러
 *
 * 자동매매 전략 설정, 상태 모니터링, 제어 기능을 제공
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/trading")
@RequiredArgsConstructor
@Tag(name = "AutoTrading", description = "자동매매 API")
public class AutoTradingController {

    private final AutoTradingService autoTradingService;

    @Operation(
        summary = "자동매매 설정 생성",
        description = "새로운 자동매매 설정을 생성하고 저장합니다."
    )
    @PostMapping("/config")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<AutoTradingConfigDto.Response>> createConfig(
            @Valid @RequestBody AutoTradingConfigDto.CreateRequest request
    ) {
        log.info("자동매매 설정 생성 요청 - 전략: {}, 종목: {}, 투자금: {}",
                request.strategyName(), request.symbol(), request.capital());

        try {
            AutoTradingConfigDto.Response response = autoTradingService.createConfig(request);
            
            return ResponseEntity.ok(ApiResponse.success(response,
                String.format("자동매매 설정이 생성되었습니다 - %s", response.id())));
                
        } catch (IllegalArgumentException e) {
            log.warn("자동매매 설정 생성 실패 - 잘못된 파라미터: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("설정 생성 실패: " + e.getMessage(), "INVALID_CONFIG"));
                    
        } catch (Exception e) {
            log.error("자동매매 설정 생성 중 오류 발생", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("자동매매 설정 생성 중 오류가 발생했습니다", "CONFIG_CREATE_ERROR"));
        }
    }

    @Operation(
        summary = "자동매매 설정 목록 조회",
        description = "사용자의 자동매매 설정 목록을 조회합니다."
    )
    @GetMapping("/configs")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<List<AutoTradingConfigDto.Response>>> getConfigs(
            @Parameter(description = "사용자 ID", example = "USER-123")
            @RequestParam String userId,
            
            @Parameter(description = "활성 상태 필터", example = "true")
            @RequestParam(required = false) Boolean isActive
    ) {
        log.debug("자동매매 설정 목록 조회 - 사용자: {}, 활성 상태: {}", userId, isActive);

        try {
            List<AutoTradingConfigDto.Response> configs = autoTradingService.getConfigs(userId, isActive);
            
            return ResponseEntity.ok(ApiResponse.success(configs,
                String.format("자동매매 설정 목록 조회 완료 - %d개", configs.size())));
                
        } catch (Exception e) {
            log.error("자동매매 설정 목록 조회 실패 - 사용자: {}", userId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("설정 목록 조회 중 오류가 발생했습니다", "CONFIGS_GET_ERROR"));
        }
    }

    @Operation(
        summary = "자동매매 설정 상세 조회",
        description = "특정 자동매매 설정의 상세 정보를 조회합니다."
    )
    @GetMapping("/config/{configId}")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<AutoTradingConfigDto.Response>> getConfig(
            @Parameter(description = "설정 ID", example = "CONFIG-123456")
            @PathVariable String configId
    ) {
        log.debug("자동매매 설정 상세 조회 - 설정 ID: {}", configId);

        try {
            AutoTradingConfigDto.Response config = autoTradingService.getConfig(configId);
            
            if (config == null) {
                return ResponseEntity.notFound().build();
            }
            
            return ResponseEntity.ok(ApiResponse.success(config,
                "자동매매 설정 조회 완료"));
                
        } catch (Exception e) {
            log.error("자동매매 설정 조회 실패 - 설정 ID: {}", configId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("설정 조회 중 오류가 발생했습니다", "CONFIG_GET_ERROR"));
        }
    }

    @Operation(
        summary = "자동매매 상태 조회",
        description = "자동매매의 현재 상태와 성과를 조회합니다."
    )
    @GetMapping("/status/{configId}")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<AutoTradingStatusDto.Response>> getStatus(
            @Parameter(description = "설정 ID", example = "CONFIG-123456")
            @PathVariable String configId
    ) {
        log.debug("자동매매 상태 조회 - 설정 ID: {}", configId);

        try {
            AutoTradingStatusDto.Response status = autoTradingService.getStatus(configId);
            
            if (status == null) {
                return ResponseEntity.notFound().build();
            }
            
            return ResponseEntity.ok(ApiResponse.success(status,
                "자동매매 상태 조회 완료"));
                
        } catch (Exception e) {
            log.error("자동매매 상태 조회 실패 - 설정 ID: {}", configId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("상태 조회 중 오류가 발생했습니다", "STATUS_GET_ERROR"));
        }
    }

    @Operation(
        summary = "자동매매 시작",
        description = "설정된 자동매매를 시작합니다."
    )
    @PostMapping("/config/{configId}/start")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Void>> startTrading(
            @Parameter(description = "설정 ID", example = "CONFIG-123456")
            @PathVariable String configId
    ) {
        log.info("자동매매 시작 요청 - 설정 ID: {}", configId);

        try {
            autoTradingService.startTrading(configId);
            
            return ResponseEntity.ok(ApiResponse.success(null,
                "자동매매가 시작되었습니다"));
                
        } catch (IllegalArgumentException e) {
            log.warn("자동매매 시작 실패 - 잘못된 설정: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("시작 실패: " + e.getMessage(), "INVALID_START"));
                    
        } catch (Exception e) {
            log.error("자동매매 시작 중 오류 발생 - 설정 ID: {}", configId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("자동매매 시작 중 오류가 발생했습니다", "START_ERROR"));
        }
    }

    @Operation(
        summary = "자동매매 정지",
        description = "실행 중인 자동매매를 정지합니다."
    )
    @PostMapping("/config/{configId}/stop")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Void>> stopTrading(
            @Parameter(description = "설정 ID", example = "CONFIG-123456")
            @PathVariable String configId
    ) {
        log.info("자동매매 정지 요청 - 설정 ID: {}", configId);

        try {
            autoTradingService.stopTrading(configId);
            
            return ResponseEntity.ok(ApiResponse.success(null,
                "자동매매가 정지되었습니다"));
                
        } catch (IllegalArgumentException e) {
            log.warn("자동매매 정지 실패 - 잘못된 설정: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("정지 실패: " + e.getMessage(), "INVALID_STOP"));
                    
        } catch (Exception e) {
            log.error("자동매매 정지 중 오류 발생 - 설정 ID: {}", configId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("자동매매 정지 중 오류가 발생했습니다", "STOP_ERROR"));
        }
    }

    @Operation(
        summary = "자동매매 일시정지",
        description = "실행 중인 자동매매를 일시정지합니다."
    )
    @PostMapping("/config/{configId}/pause")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Void>> pauseTrading(
            @Parameter(description = "설정 ID", example = "CONFIG-123456")
            @PathVariable String configId
    ) {
        log.info("자동매매 일시정지 요청 - 설정 ID: {}", configId);

        try {
            autoTradingService.pauseTrading(configId);
            
            return ResponseEntity.ok(ApiResponse.success(null,
                "자동매매가 일시정지되었습니다"));
                
        } catch (Exception e) {
            log.error("자동매매 일시정지 중 오류 발생 - 설정 ID: {}", configId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("일시정지 중 오류가 발생했습니다", "PAUSE_ERROR"));
        }
    }

    @Operation(
        summary = "자동매매 재개",
        description = "일시정지된 자동매매를 재개합니다."
    )
    @PostMapping("/config/{configId}/resume")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Void>> resumeTrading(
            @Parameter(description = "설정 ID", example = "CONFIG-123456")
            @PathVariable String configId
    ) {
        log.info("자동매매 재개 요청 - 설정 ID: {}", configId);

        try {
            autoTradingService.resumeTrading(configId);
            
            return ResponseEntity.ok(ApiResponse.success(null,
                "자동매매가 재개되었습니다"));
                
        } catch (Exception e) {
            log.error("자동매매 재개 중 오류 발생 - 설정 ID: {}", configId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("재개 중 오류가 발생했습니다", "RESUME_ERROR"));
        }
    }

    @Operation(
        summary = "자동매매 설정 삭제",
        description = "자동매매 설정을 삭제합니다. 실행 중인 경우 먼저 정지됩니다."
    )
    @DeleteMapping("/config/{configId}")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Void>> deleteConfig(
            @Parameter(description = "설정 ID", example = "CONFIG-123456")
            @PathVariable String configId
    ) {
        log.info("자동매매 설정 삭제 요청 - 설정 ID: {}", configId);

        try {
            autoTradingService.deleteConfig(configId);
            
            return ResponseEntity.ok(ApiResponse.success(null,
                "자동매매 설정이 삭제되었습니다"));
                
        } catch (Exception e) {
            log.error("자동매매 설정 삭제 중 오류 발생 - 설정 ID: {}", configId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("설정 삭제 중 오류가 발생했습니다", "DELETE_ERROR"));
        }
    }
}