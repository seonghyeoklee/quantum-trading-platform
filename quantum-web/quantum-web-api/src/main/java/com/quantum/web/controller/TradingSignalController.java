package com.quantum.web.controller;

import com.quantum.web.dto.ApiResponse;
import com.quantum.web.service.TradingSignalService;
import com.quantum.web.dto.TradingSignalDto;
import com.quantum.web.dto.OrderExecutionResultDto;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

/**
 * 자동매매 전략 신호 처리 컨트롤러
 * 
 * Python 전략 엔진에서 생성된 매매신호를 받아서 실제 주문으로 처리
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/trading/signals")
@RequiredArgsConstructor
public class TradingSignalController {
    
    private final TradingSignalService tradingSignalService;
    
    /**
     * Python 전략에서 매매신호 수신
     * 
     * @param signalDto 매매신호 데이터
     * @return 신호 처리 결과
     */
    @PostMapping("/receive")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<OrderExecutionResultDto>> receiveSignal(
            @Valid @RequestBody TradingSignalDto signalDto) {
        
        log.info("매매신호 수신: {} - {} (종목: {}, 신뢰도: {})", 
                signalDto.getStrategyName(), 
                signalDto.getSignalType(), 
                signalDto.getSymbol(),
                signalDto.getConfidence());
        
        try {
            // 매매신호를 실제 주문으로 처리
            OrderExecutionResultDto result = tradingSignalService.processSignal(signalDto);
            
            return ResponseEntity.ok(ApiResponse.success(
                "매매신호 처리 완료", 
                result
            ));
            
        } catch (Exception e) {
            log.error("매매신호 처리 실패: {}", e.getMessage(), e);
            return ResponseEntity.badRequest().body(ApiResponse.error(
                "매매신호 처리 실패: " + e.getMessage()
            ));
        }
    }
    
    /**
     * 최근 매매신호 조회
     * 
     * @param limit 조회할 신호 개수
     * @return 최근 매매신호 목록
     */
    @GetMapping("/recent")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<List<TradingSignalDto>>> getRecentSignals(
            @RequestParam(defaultValue = "20") int limit) {
        
        try {
            List<TradingSignalDto> signals = tradingSignalService.getRecentSignals(limit);
            
            return ResponseEntity.ok(ApiResponse.success(
                "최근 매매신호 조회 완료",
                signals
            ));
            
        } catch (Exception e) {
            log.error("매매신호 조회 실패: {}", e.getMessage(), e);
            return ResponseEntity.badRequest().body(ApiResponse.error(
                "매매신호 조회 실패: " + e.getMessage()
            ));
        }
    }
    
    /**
     * 전략별 매매신호 통계
     * 
     * @param strategyName 전략명
     * @return 전략 통계 정보
     */
    @GetMapping("/stats/{strategyName}")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Object>> getStrategyStats(
            @PathVariable String strategyName) {
        
        try {
            var stats = tradingSignalService.getStrategyStats(strategyName);
            
            return ResponseEntity.ok(ApiResponse.success(
                "전략 통계 조회 완료",
                stats
            ));
            
        } catch (Exception e) {
            log.error("전략 통계 조회 실패: {}", e.getMessage(), e);
            return ResponseEntity.badRequest().body(ApiResponse.error(
                "전략 통계 조회 실패: " + e.getMessage()
            ));
        }
    }
    
    /**
     * 전략 신호 활성화/비활성화
     * 
     * @param strategyName 전략명
     * @param enabled 활성화 여부
     * @return 처리 결과
     */
    @PatchMapping("/strategies/{strategyName}/enabled")
    @PreAuthorize("hasAnyRole('MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Void>> setStrategyEnabled(
            @PathVariable String strategyName,
            @RequestParam boolean enabled) {
        
        try {
            tradingSignalService.setStrategyEnabled(strategyName, enabled);
            
            String message = enabled ? "전략 활성화 완료" : "전략 비활성화 완료";
            return ResponseEntity.ok(ApiResponse.success(message));
            
        } catch (Exception e) {
            log.error("전략 활성화 설정 실패: {}", e.getMessage(), e);
            return ResponseEntity.badRequest().body(ApiResponse.error(
                "전략 활성화 설정 실패: " + e.getMessage()
            ));
        }
    }
    
    /**
     * 매매신호 실행 모드 설정 (실투자/모의투자)
     * 
     * @param dryRun 모의투자 여부 (true: 모의투자, false: 실투자)
     * @return 처리 결과
     */
    @PatchMapping("/execution-mode")
    @PreAuthorize("hasRole('ADMIN')")  // 실투자 모드는 관리자만 변경 가능
    public ResponseEntity<ApiResponse<Void>> setExecutionMode(
            @RequestParam boolean dryRun) {
        
        try {
            tradingSignalService.setExecutionMode(dryRun);
            
            String mode = dryRun ? "모의투자" : "실투자";
            log.warn("매매실행 모드 변경: {}", mode);
            
            return ResponseEntity.ok(ApiResponse.success(
                "실행 모드가 " + mode + "로 변경되었습니다"
            ));
            
        } catch (Exception e) {
            log.error("실행 모드 설정 실패: {}", e.getMessage(), e);
            return ResponseEntity.badRequest().body(ApiResponse.error(
                "실행 모드 설정 실패: " + e.getMessage()
            ));
        }
    }
    
    /**
     * 시스템 상태 조회
     * 
     * @return 자동매매 시스템 상태
     */
    @GetMapping("/system/status")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Object>> getSystemStatus() {
        
        try {
            var status = tradingSignalService.getSystemStatus();
            
            return ResponseEntity.ok(ApiResponse.success(
                "시스템 상태 조회 완료",
                status
            ));
            
        } catch (Exception e) {
            log.error("시스템 상태 조회 실패: {}", e.getMessage(), e);
            return ResponseEntity.badRequest().body(ApiResponse.error(
                "시스템 상태 조회 실패: " + e.getMessage()
            ));
        }
    }
    
    /**
     * 매매신호 강제 처리 (테스트용)
     * 
     * @param signalDto 테스트할 매매신호
     * @return 처리 결과
     */
    @PostMapping("/test")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<OrderExecutionResultDto>> testSignal(
            @Valid @RequestBody TradingSignalDto signalDto) {
        
        log.info("테스트 매매신호 처리: {} - {} (종목: {})", 
                signalDto.getStrategyName(), 
                signalDto.getSignalType(), 
                signalDto.getSymbol());
        
        try {
            // 강제로 테스트 모드로 처리
            signalDto.setDryRun(true);
            OrderExecutionResultDto result = tradingSignalService.processSignal(signalDto);
            
            return ResponseEntity.ok(ApiResponse.success(
                "테스트 매매신호 처리 완료", 
                result
            ));
            
        } catch (Exception e) {
            log.error("테스트 매매신호 처리 실패: {}", e.getMessage(), e);
            return ResponseEntity.badRequest().body(ApiResponse.error(
                "테스트 매매신호 처리 실패: " + e.getMessage()
            ));
        }
    }
}