package com.quantum.web.controller;

import com.quantum.web.events.RealtimeOrderData;
import com.quantum.web.events.RealtimeQuoteData;
import com.quantum.web.events.RealtimeScreenerData;
import com.quantum.web.service.RealtimeDataCacheService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 실시간 데이터 API 컨트롤러
 * 캐시된 실시간 데이터 조회 및 WebSocket 연결 관리
 */
@RestController
@RequestMapping("/api/v1/realtime")
@Tag(name = "실시간 데이터", description = "실시간 주식 시세, 주문, 스크리너 데이터 API")
@CrossOrigin(origins = "*")
public class RealtimeController {

    private static final Logger logger = LoggerFactory.getLogger(RealtimeController.class);

    private final RealtimeDataCacheService cacheService;
    private final SimpMessagingTemplate messagingTemplate;

    public RealtimeController(RealtimeDataCacheService cacheService, SimpMessagingTemplate messagingTemplate) {
        this.cacheService = cacheService;
        this.messagingTemplate = messagingTemplate;
    }

    /**
     * 실시간 주식 시세 조회
     */
    @GetMapping("/quote/{symbol}")
    @Operation(summary = "실시간 주식 시세 조회", description = "지정된 종목의 실시간 시세 데이터를 조회합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "시세 조회 성공"),
        @ApiResponse(responseCode = "404", description = "종목 데이터 없음")
    })
    public ResponseEntity<RealtimeQuoteData> getRealtimeQuote(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable String symbol) {
        
        logger.debug("Getting realtime quote for symbol: {}", symbol);
        
        RealtimeQuoteData quote = cacheService.getQuoteData(symbol);
        if (quote != null) {
            return ResponseEntity.ok(quote);
        } else {
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * 모든 캐시된 실시간 시세 조회
     */
    @GetMapping("/quotes")
    @Operation(summary = "전체 실시간 시세 조회", description = "캐시된 모든 종목의 실시간 시세 데이터를 조회합니다")
    @ApiResponse(responseCode = "200", description = "전체 시세 조회 성공")
    public ResponseEntity<List<RealtimeQuoteData>> getAllRealtimeQuotes() {
        
        logger.debug("Getting all realtime quotes");
        
        List<RealtimeQuoteData> quotes = cacheService.getAllQuoteData();
        return ResponseEntity.ok(quotes);
    }

    /**
     * 계좌별 실시간 주문 데이터 조회
     */
    @GetMapping("/orders/{accountNumber}")
    @Operation(summary = "계좌별 주문 데이터 조회", description = "지정된 계좌의 실시간 주문 데이터를 조회합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "주문 데이터 조회 성공"),
        @ApiResponse(responseCode = "404", description = "계좌 데이터 없음")
    })
    public ResponseEntity<List<RealtimeOrderData>> getRealtimeOrders(
            @Parameter(description = "계좌번호", example = "12345678-01")
            @PathVariable String accountNumber) {
        
        logger.debug("Getting realtime orders for account: {}", accountNumber);
        
        List<RealtimeOrderData> orders = cacheService.getOrderDataByAccount(accountNumber);
        return ResponseEntity.ok(orders);
    }

    /**
     * 스크리너 결과 조회
     */
    @GetMapping("/screener/{conditionName}")
    @Operation(summary = "스크리너 결과 조회", description = "지정된 조건검색의 실시간 결과를 조회합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "스크리너 결과 조회 성공"),
        @ApiResponse(responseCode = "404", description = "조건검색 데이터 없음")
    })
    public ResponseEntity<RealtimeScreenerData> getScreenerData(
            @Parameter(description = "조건검색명", example = "상승주")
            @PathVariable String conditionName) {
        
        logger.debug("Getting screener data for condition: {}", conditionName);
        
        RealtimeScreenerData screenerData = cacheService.getScreenerData(conditionName);
        if (screenerData != null) {
            return ResponseEntity.ok(screenerData);
        } else {
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * 실시간 데이터 수동 브로드캐스트 (테스트용)
     */
    @PostMapping("/broadcast/quote/{symbol}")
    @Operation(summary = "실시간 시세 브로드캐스트", description = "지정된 종목의 시세를 WebSocket으로 브로드캐스트합니다 (테스트용)")
    @ApiResponse(responseCode = "200", description = "브로드캐스트 성공")
    public ResponseEntity<Map<String, String>> broadcastQuote(
            @Parameter(description = "종목코드", example = "005930")
            @PathVariable String symbol) {
        
        logger.debug("Broadcasting quote for symbol: {}", symbol);
        
        RealtimeQuoteData quote = cacheService.getQuoteData(symbol);
        if (quote != null) {
            messagingTemplate.convertAndSend("/topic/quote/" + symbol, quote);
            messagingTemplate.convertAndSend("/topic/quote/all", quote);
            
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "Quote broadcasted for symbol: " + symbol
            ));
        } else {
            return ResponseEntity.ok(Map.of(
                "status", "warning",
                "message", "No cached data for symbol: " + symbol
            ));
        }
    }

    /**
     * WebSocket 연결 테스트
     */
    @PostMapping("/test/connection")
    @Operation(summary = "WebSocket 연결 테스트", description = "WebSocket 연결 상태를 테스트합니다")
    @ApiResponse(responseCode = "200", description = "테스트 메시지 전송 완료")
    public ResponseEntity<Map<String, String>> testWebSocketConnection() {
        
        logger.debug("Testing WebSocket connection");
        
        Map<String, Object> testMessage = Map.of(
            "type", "connection_test",
            "message", "WebSocket connection is working",
            "timestamp", System.currentTimeMillis()
        );
        
        messagingTemplate.convertAndSend("/topic/test", testMessage);
        
        return ResponseEntity.ok(Map.of(
            "status", "success",
            "message", "Test message sent to /topic/test"
        ));
    }

    /**
     * 캐시 상태 조회
     */
    @GetMapping("/cache/status")
    @Operation(summary = "캐시 상태 조회", description = "실시간 데이터 캐시의 전체 상태를 조회합니다")
    @ApiResponse(responseCode = "200", description = "캐시 상태 조회 성공")
    public ResponseEntity<Map<String, Object>> getCacheStatus() {
        
        logger.debug("Getting cache status");
        
        List<RealtimeQuoteData> quotes = cacheService.getAllQuoteData();
        
        Map<String, Object> status = Map.of(
            "cached_quotes_count", quotes.size(),
            "cached_symbols", quotes.stream().map(RealtimeQuoteData::getSymbol).toList(),
            "timestamp", System.currentTimeMillis()
        );
        
        return ResponseEntity.ok(status);
    }

    /**
     * 캐시 삭제 (관리용)
     */
    @DeleteMapping("/cache")
    @Operation(summary = "전체 캐시 삭제", description = "모든 실시간 데이터 캐시를 삭제합니다 (관리용)")
    @ApiResponse(responseCode = "200", description = "캐시 삭제 완료")
    public ResponseEntity<Map<String, String>> evictAllCache() {
        
        logger.info("Evicting all realtime data cache");
        
        cacheService.evictAllRealtimeCache();
        
        return ResponseEntity.ok(Map.of(
            "status", "success",
            "message", "All realtime cache evicted"
        ));
    }
}