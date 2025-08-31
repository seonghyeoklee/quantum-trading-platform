package com.quantum.web.controller;

import com.quantum.web.dto.ApiResponse;
import com.quantum.web.service.TradingAnalysisService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 종목 분석 컨트롤러
 *
 * 자동매매를 위한 종목 분석 및 전략 적합성 평가 API를 제공
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/trading")
@RequiredArgsConstructor
@Tag(name = "TradingAnalysis", description = "종목 분석 API")
public class TradingAnalysisController {

    private final TradingAnalysisService tradingAnalysisService;

    @Operation(
        summary = "종목 분석",
        description = "지정된 종목의 기술적 지표를 분석하고 현재 상태를 반환합니다."
    )
    @GetMapping("/analysis/{symbol}")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Map<String, Object>>> analyzeStock(
            @Parameter(description = "종목 코드", example = "005930")
            @PathVariable String symbol
    ) {
        log.info("종목 분석 요청 - 종목: {}", symbol);

        try {
            Map<String, Object> analysis = tradingAnalysisService.analyzeStock(symbol);
            
            return ResponseEntity.ok(ApiResponse.success(analysis,
                String.format("%s 종목 분석 완료", symbol)));
                
        } catch (IllegalArgumentException e) {
            log.warn("종목 분석 실패 - 잘못된 파라미터: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("분석 실패: " + e.getMessage(), "INVALID_SYMBOL"));
                    
        } catch (Exception e) {
            log.error("종목 분석 중 오류 발생 - 종목: {}", symbol, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("종목 분석 중 오류가 발생했습니다", "ANALYSIS_ERROR"));
        }
    }

    @Operation(
        summary = "전략 적합성 분석",
        description = "특정 전략에 대한 종목의 적합성을 분석하고 점수를 반환합니다."
    )
    @GetMapping("/analysis/{symbol}/strategy/{strategyName}")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Map<String, Object>>> analyzeStrategyFit(
            @Parameter(description = "종목 코드", example = "005930")
            @PathVariable String symbol,
            
            @Parameter(description = "전략명", example = "moving_average_crossover")
            @PathVariable String strategyName
    ) {
        log.info("전략 적합성 분석 요청 - 종목: {}, 전략: {}", symbol, strategyName);

        try {
            Map<String, Object> analysis = tradingAnalysisService.analyzeStrategyFit(symbol, strategyName);
            
            return ResponseEntity.ok(ApiResponse.success(analysis,
                String.format("%s 종목의 %s 전략 적합성 분석 완료", symbol, strategyName)));
                
        } catch (IllegalArgumentException e) {
            log.warn("전략 적합성 분석 실패 - 잘못된 파라미터: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("분석 실패: " + e.getMessage(), "INVALID_PARAMETER"));
                    
        } catch (Exception e) {
            log.error("전략 적합성 분석 중 오류 발생 - 종목: {}, 전략: {}", symbol, strategyName, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("전략 적합성 분석 중 오류가 발생했습니다", "STRATEGY_ANALYSIS_ERROR"));
        }
    }

    @Operation(
        summary = "시장 전체 분석",
        description = "현재 시장 상황을 분석하고 자동매매에 적합한 환경인지 판단합니다."
    )
    @GetMapping("/analysis/market")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Map<String, Object>>> analyzeMarket() {
        log.info("시장 전체 분석 요청");

        try {
            Map<String, Object> marketAnalysis = tradingAnalysisService.analyzeMarket();
            
            return ResponseEntity.ok(ApiResponse.success(marketAnalysis,
                "시장 분석 완료"));
                
        } catch (Exception e) {
            log.error("시장 분석 중 오류 발생", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("시장 분석 중 오류가 발생했습니다", "MARKET_ANALYSIS_ERROR"));
        }
    }

    @Operation(
        summary = "종목 리스트 분석",
        description = "여러 종목을 동시에 분석하고 랭킹을 반환합니다."
    )
    @PostMapping("/analysis/batch")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Map<String, Object>>> analyzeBatchStocks(
            @Parameter(description = "분석할 종목 코드 목록")
            @RequestBody BatchAnalysisRequest request
    ) {
        log.info("배치 종목 분석 요청 - 종목 수: {}, 전략: {}", 
                request.symbols().size(), request.strategyName());

        try {
            Map<String, Object> batchAnalysis = tradingAnalysisService.analyzeBatchStocks(
                    request.symbols(), request.strategyName());
            
            return ResponseEntity.ok(ApiResponse.success(batchAnalysis,
                String.format("%d개 종목 배치 분석 완료", request.symbols().size())));
                
        } catch (IllegalArgumentException e) {
            log.warn("배치 분석 실패 - 잘못된 파라미터: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("분석 실패: " + e.getMessage(), "INVALID_BATCH_REQUEST"));
                    
        } catch (Exception e) {
            log.error("배치 분석 중 오류 발생", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("배치 분석 중 오류가 발생했습니다", "BATCH_ANALYSIS_ERROR"));
        }
    }

    @Operation(
        summary = "실시간 시장 상태",
        description = "현재 시장의 실시간 상태 정보를 반환합니다."
    )
    @GetMapping("/analysis/realtime-market")
    @PreAuthorize("hasAnyRole('TRADER', 'MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getRealtimeMarketStatus() {
        log.debug("실시간 시장 상태 조회 요청");

        try {
            Map<String, Object> realtimeStatus = tradingAnalysisService.getRealtimeMarketStatus();
            
            return ResponseEntity.ok(ApiResponse.success(realtimeStatus,
                "실시간 시장 상태 조회 완료"));
                
        } catch (Exception e) {
            log.error("실시간 시장 상태 조회 중 오류 발생", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("실시간 시장 상태 조회 중 오류가 발생했습니다", "REALTIME_STATUS_ERROR"));
        }
    }

    @Operation(
        summary = "백테스팅 분석",
        description = "특정 전략과 종목에 대한 백테스팅 결과를 반환합니다."
    )
    @GetMapping("/analysis/{symbol}/backtest/{strategyName}")
    @PreAuthorize("hasAnyRole('MANAGER', 'ADMIN')")
    public ResponseEntity<ApiResponse<Map<String, Object>>> runBacktest(
            @Parameter(description = "종목 코드", example = "005930")
            @PathVariable String symbol,
            
            @Parameter(description = "전략명", example = "moving_average_crossover")
            @PathVariable String strategyName,
            
            @Parameter(description = "백테스팅 시작일", example = "2023-01-01")
            @RequestParam(required = false, defaultValue = "2023-01-01") String startDate,
            
            @Parameter(description = "백테스팅 종료일", example = "2023-12-31")
            @RequestParam(required = false, defaultValue = "2023-12-31") String endDate,
            
            @Parameter(description = "초기 자본금", example = "10000000")
            @RequestParam(required = false, defaultValue = "10000000") Long initialCapital
    ) {
        log.info("백테스팅 요청 - 종목: {}, 전략: {}, 기간: {} ~ {}", 
                symbol, strategyName, startDate, endDate);

        try {
            Map<String, Object> backtestResult = tradingAnalysisService.runBacktest(
                    symbol, strategyName, startDate, endDate, initialCapital);
            
            return ResponseEntity.ok(ApiResponse.success(backtestResult,
                "백테스팅 분석 완료"));
                
        } catch (IllegalArgumentException e) {
            log.warn("백테스팅 실패 - 잘못된 파라미터: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("백테스팅 실패: " + e.getMessage(), "INVALID_BACKTEST_PARAMETER"));
                    
        } catch (Exception e) {
            log.error("백테스팅 중 오류 발생 - 종목: {}, 전략: {}", symbol, strategyName, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("백테스팅 중 오류가 발생했습니다", "BACKTEST_ERROR"));
        }
    }

    /**
     * 배치 분석 요청 DTO
     */
    public record BatchAnalysisRequest(
            java.util.List<String> symbols,
            String strategyName
    ) {}
}