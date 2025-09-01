package com.quantum.web.controller;

import com.quantum.web.dto.ApiResponse;
import com.quantum.web.security.UserPrincipal;
import com.quantum.web.service.TradingModeDetectionService;
import com.quantum.web.service.TradingSignalService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 거래 모드 관리 REST API
 * 
 * API 키 패턴을 기반으로 한 자동 거래 모드 탐지 및 관리 기능을 제공합니다.
 */
@RestController
@RequestMapping("/api/v1/trading-mode")
@RequiredArgsConstructor
@Slf4j
public class TradingModeController {
    
    private final TradingModeDetectionService tradingModeDetectionService;
    private final TradingSignalService tradingSignalService;
    
    /**
     * 현재 사용자의 거래 모드 자동 탐지
     * 
     * GET /api/v1/trading-mode/detect
     */
    @GetMapping("/detect")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<ApiResponse<TradingModeDetectionService.TradingModeInfo>> detectTradingMode(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        
        try {
            String userId = userPrincipal.getId();
            log.info("사용자 {} 거래 모드 탐지 요청", userId);
            
            TradingModeDetectionService.TradingModeInfo modeInfo = 
                tradingSignalService.detectUserTradingMode(userId);
                
            return ResponseEntity.ok(ApiResponse.success(modeInfo, "거래 모드 탐지 완료"));
            
        } catch (Exception e) {
            log.error("거래 모드 탐지 중 오류 발생", e);
            return ResponseEntity.internalServerError()
                .body(ApiResponse.error("거래 모드 탐지에 실패했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * 현재 사용자의 간단한 거래 모드 정보
     * 
     * GET /api/v1/trading-mode/status
     */
    @GetMapping("/status")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getTradingModeStatus(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        
        try {
            String userId = userPrincipal.getId();
            log.debug("사용자 {} 거래 모드 상태 조회", userId);
            
            String currentMode = tradingSignalService.getActualTradingMode(userId);
            boolean isProduction = tradingSignalService.isProductionMode(userId);
            boolean isSandbox = tradingSignalService.isSandboxMode(userId);
            
            Map<String, Object> status = Map.of(
                "userId", userId,
                "tradingMode", currentMode,
                "isProduction", isProduction,
                "isSandbox", isSandbox,
                "modeDisplayName", getModeDisplayName(currentMode)
            );
            
            return ResponseEntity.ok(ApiResponse.success(status, "거래 모드 상태 조회 완료"));
            
        } catch (Exception e) {
            log.error("거래 모드 상태 조회 중 오류 발생", e);
            return ResponseEntity.internalServerError()
                .body(ApiResponse.error("거래 모드 상태 조회에 실패했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * 특정 사용자의 거래 모드 탐지 (관리자용)
     * 
     * GET /api/v1/trading-mode/detect/{userId}
     */
    @GetMapping("/detect/{userId}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<TradingModeDetectionService.TradingModeInfo>> detectUserTradingMode(
            @PathVariable String userId) {
        
        try {
            log.info("관리자가 사용자 {} 거래 모드 탐지 요청", userId);
            
            TradingModeDetectionService.TradingModeInfo modeInfo = 
                tradingSignalService.detectUserTradingMode(userId);
                
            return ResponseEntity.ok(ApiResponse.success(modeInfo, 
                String.format("사용자 %s 거래 모드 탐지 완료", userId)));
            
        } catch (Exception e) {
            log.error("사용자 {} 거래 모드 탐지 중 오류 발생", userId, e);
            return ResponseEntity.internalServerError()
                .body(ApiResponse.error("거래 모드 탐지에 실패했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * 모든 사용자 거래 모드 일괄 재탐지 (관리자용)
     * 
     * POST /api/v1/trading-mode/batch-detect
     */
    @PostMapping("/batch-detect")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<TradingModeDetectionService.BatchDetectionResult>> batchDetectTradingModes() {
        
        try {
            log.info("관리자가 모든 사용자 거래 모드 일괄 재탐지 요청");
            
            TradingModeDetectionService.BatchDetectionResult result = 
                tradingModeDetectionService.batchDetectTradingModes();
                
            return ResponseEntity.ok(ApiResponse.success(result, "일괄 거래 모드 탐지 완료"));
            
        } catch (Exception e) {
            log.error("일괄 거래 모드 탐지 중 오류 발생", e);
            return ResponseEntity.internalServerError()
                .body(ApiResponse.error("일괄 거래 모드 탐지에 실패했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * 거래 모드 패턴 검증 (관리자용 디버깅)
     * 
     * POST /api/v1/trading-mode/validate-pattern
     */
    @PostMapping("/validate-pattern")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<Map<String, Object>>> validateKeyPattern(
            @RequestBody KeyPatternValidationRequest request) {
        
        try {
            log.info("관리자가 API 키 패턴 검증 요청");
            
            // 실제로는 TradingModeDetectionService 내부 로직을 호출하여 패턴 검증
            // 여기서는 간단한 패턴 분석 결과만 반환
            Map<String, Object> result = Map.of(
                "appKey", maskKey(request.getAppKey()),
                "secretKey", maskKey(request.getSecretKey()),
                "detectedMode", analyzeKeyPattern(request.getAppKey(), request.getSecretKey()),
                "confidence", calculatePatternConfidence(request.getAppKey(), request.getSecretKey()),
                "validationMessages", getValidationMessages(request.getAppKey(), request.getSecretKey())
            );
            
            return ResponseEntity.ok(ApiResponse.success(result, "API 키 패턴 검증 완료"));
            
        } catch (Exception e) {
            log.error("API 키 패턴 검증 중 오류 발생", e);
            return ResponseEntity.internalServerError()
                .body(ApiResponse.error("패턴 검증에 실패했습니다: " + e.getMessage()));
        }
    }
    
    // Helper methods
    
    private String getModeDisplayName(String modeCode) {
        return switch (modeCode) {
            case "PRODUCTION" -> "실전투자";
            case "SANDBOX" -> "모의투자";
            default -> "알 수 없음";
        };
    }
    
    private String maskKey(String key) {
        if (key == null || key.length() < 8) {
            return "INVALID_KEY";
        }
        return key.substring(0, 4) + "****" + key.substring(key.length() - 4);
    }
    
    private String analyzeKeyPattern(String appKey, String secretKey) {
        // 간단한 패턴 분석 (실제로는 TradingModeDetectionService 로직 사용)
        if (appKey.contains("_TEST") || appKey.contains("_SB") || secretKey.contains("_TEST")) {
            return "SANDBOX";
        } else if (appKey.length() >= 32 && secretKey.length() >= 32) {
            return "PRODUCTION";
        } else {
            return "UNKNOWN";
        }
    }
    
    private double calculatePatternConfidence(String appKey, String secretKey) {
        // 간단한 신뢰도 계산
        int score = 0;
        if (appKey != null && appKey.length() >= 32) score += 30;
        if (secretKey != null && secretKey.length() >= 32) score += 30;
        if (!appKey.contains("test") && !appKey.contains("demo")) score += 20;
        if (!secretKey.contains("test") && !secretKey.contains("demo")) score += 20;
        
        return score / 100.0;
    }
    
    private String[] getValidationMessages(String appKey, String secretKey) {
        java.util.List<String> messages = new java.util.ArrayList<>();
        
        if (appKey == null || appKey.length() < 16) {
            messages.add("App Key가 너무 짧습니다");
        }
        if (secretKey == null || secretKey.length() < 16) {
            messages.add("Secret Key가 너무 짧습니다");
        }
        if (appKey != null && (appKey.contains("test") || appKey.contains("demo"))) {
            messages.add("모의투자용 App Key로 판단됩니다");
        }
        if (secretKey != null && (secretKey.contains("test") || secretKey.contains("demo"))) {
            messages.add("모의투자용 Secret Key로 판단됩니다");
        }
        
        if (messages.isEmpty()) {
            messages.add("유효한 키 형식입니다");
        }
        
        return messages.toArray(new String[0]);
    }
    
    // Request DTO
    
    @lombok.Data
    public static class KeyPatternValidationRequest {
        private String appKey;
        private String secretKey;
    }
}