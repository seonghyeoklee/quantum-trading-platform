package com.quantum.api.kiwoom.controller;

import com.quantum.api.kiwoom.dto.stock.StockInfoRequest;
import com.quantum.api.kiwoom.dto.stock.StockInfoResponse;
import com.quantum.api.kiwoom.service.StockInfoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

/**
 * 키움증권 주식 기본정보 API 컨트롤러
 * 키움 API: /api/dostk/stkinfo
 * api-id: ka10001
 */
@RestController
@RequestMapping("/api/dostk")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "주식정보", description = "키움증권 주식 기본정보 API")
public class StockInfoController {
    
    private final StockInfoService stockInfoService;
    
    /**
     * 주식 기본정보 조회 (키움 API 스펙)
     * POST /api/dostk/stkinfo
     */
    @PostMapping("/stkinfo")
    @Operation(
        summary = "주식 기본정보 조회",
        description = "종목코드를 입력받아 주식의 기본정보를 조회합니다. " +
                      "PER, PBR, EPS, BPS 등 투자지표와 시가총액, 거래량 등의 정보를 제공합니다."
    )
    public Mono<ResponseEntity<StockInfoResponse>> getStockInfo(
            @RequestHeader("authorization") String authorization,
            @RequestHeader(value = "cont-yn", defaultValue = "N") 
            @Parameter(description = "연속조회여부 (Y/N)") String contYn,
            @RequestHeader(value = "next-key", defaultValue = "") 
            @Parameter(description = "연속조회키") String nextKey,
            @RequestHeader("api-id") 
            @Parameter(description = "API ID", example = "ka10001") String apiId,
            @RequestBody StockInfoRequest request) {
        
        log.info("주식 기본정보 조회 요청 - 종목코드: {}, api-id: {}, 연속조회: {}", 
                request.getStockCode(), apiId, contYn);
        
        // Bearer 토큰 추출
        String accessToken = extractToken(authorization);
        
        return stockInfoService.getStockInfo(
                request.getStockCode(), 
                accessToken, 
                contYn, 
                nextKey
        )
        .map(response -> {
            // 키움 API 스펙에 따른 응답 헤더 설정
            return ResponseEntity.ok()
                    .header("cont-yn", "N")  // 연속조회 없음
                    .header("next-key", "")   // 다음 키 없음
                    .header("api-id", apiId)
                    .body(response);
        })
        .doOnSuccess(response -> 
            log.info("주식 기본정보 조회 완료 - 종목: {}", request.getStockCode()))
        .doOnError(error -> 
            log.error("주식 기본정보 조회 실패 - 종목: {}", request.getStockCode(), error));
    }
    
    /**
     * 주식 기본정보 간편 조회 (GET 방식)
     * GET /api/dostk/stkinfo/{stockCode}
     */
    @GetMapping("/stkinfo/{stockCode}")
    @Operation(
        summary = "주식 기본정보 간편 조회",
        description = "GET 방식으로 종목코드만 입력받아 주식 기본정보를 조회합니다."
    )
    public Mono<ResponseEntity<StockInfoResponse>> getStockInfoSimple(
            @PathVariable 
            @Parameter(description = "종목코드", example = "005930") String stockCode,
            @RequestHeader("authorization") String authorization) {
        
        log.info("주식 기본정보 간편 조회 - 종목코드: {}", stockCode);
        
        String accessToken = extractToken(authorization);
        
        return stockInfoService.getStockInfo(stockCode, accessToken)
                .map(ResponseEntity::ok)
                .doOnSuccess(response -> 
                    log.info("주식 기본정보 간편 조회 완료 - 종목: {}", stockCode))
                .doOnError(error -> 
                    log.error("주식 기본정보 간편 조회 실패 - 종목: {}", stockCode, error));
    }
    
    /**
     * 여러 종목 기본정보 일괄 조회
     * POST /api/dostk/stkinfo/batch
     */
    @PostMapping("/stkinfo/batch")
    @Operation(
        summary = "여러 종목 기본정보 일괄 조회",
        description = "여러 종목코드를 입력받아 기본정보를 일괄 조회합니다."
    )
    public Mono<ResponseEntity<Map<String, StockInfoResponse>>> getMultipleStockInfo(
            @RequestHeader("authorization") String authorization,
            @RequestBody 
            @Parameter(description = "종목코드 목록", example = "[\"005930\", \"000660\", \"035420\"]") 
            List<String> stockCodes) {
        
        log.info("여러 종목 기본정보 일괄 조회 - 종목 수: {}", stockCodes.size());
        
        String accessToken = extractToken(authorization);
        
        return stockInfoService.getMultipleStockInfo(stockCodes, accessToken)
                .map(ResponseEntity::ok)
                .doOnSuccess(response -> 
                    log.info("여러 종목 기본정보 일괄 조회 완료 - 성공: {}/{}", 
                            response.size(), stockCodes.size()))
                .doOnError(error -> 
                    log.error("여러 종목 기본정보 일괄 조회 실패", error));
    }
    
    /**
     * 주식 기본정보 조회 (토큰 자동 관리)
     * POST /api/dostk/stkinfo/auto
     */
    @PostMapping("/stkinfo/auto")
    @Operation(
        summary = "주식 기본정보 조회 (토큰 자동 관리)",
        description = "앱키와 시크릿을 입력받아 토큰을 자동으로 관리하며 주식 기본정보를 조회합니다."
    )
    public Mono<ResponseEntity<StockInfoResponse>> getStockInfoWithAuth(
            @RequestParam 
            @Parameter(description = "종목코드", example = "005930") String stockCode,
            @RequestParam 
            @Parameter(description = "앱키", required = true) String appKey,
            @RequestParam 
            @Parameter(description = "앱시크릿", required = true) String appSecret) {
        
        log.info("주식 기본정보 조회 (토큰 자동) - 종목코드: {}", stockCode);
        
        return stockInfoService.getStockInfoWithAuth(stockCode, appKey, appSecret)
                .map(ResponseEntity::ok)
                .doOnSuccess(response -> 
                    log.info("주식 기본정보 조회 완료 (토큰 자동) - 종목: {}", stockCode))
                .doOnError(error -> 
                    log.error("주식 기본정보 조회 실패 (토큰 자동) - 종목: {}", stockCode, error));
    }
    
    /**
     * Authorization 헤더에서 토큰 추출
     */
    private String extractToken(String authHeader) {
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        return authHeader;
    }
}