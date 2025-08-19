package com.quantum.api.kiwoom.controller;

import com.quantum.api.kiwoom.dto.order.OrderRequest;
import com.quantum.api.kiwoom.dto.order.OrderResponse;
import com.quantum.api.kiwoom.dto.order.OrderCancelRequest;
import com.quantum.api.kiwoom.dto.order.OrderModifyRequest;
import com.quantum.api.kiwoom.dto.stock.*;
import com.quantum.api.kiwoom.service.DomesticStockService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;

/**
 * 국내주식 거래 API 컨트롤러
 * 자동매매를 위한 핵심 거래 기능 제공
 */
@RestController
@RequestMapping("/api/v1/domestic-stock")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "국내주식", description = "국내주식 거래 및 조회 API")
public class DomesticStockController {
    
    private final DomesticStockService domesticStockService;
    
    // ========== 주문 관련 API ==========
    
    @PostMapping("/orders")
    @Operation(summary = "주식 주문", description = "국내주식 매수/매도 주문")
    public Mono<ResponseEntity<OrderResponse>> placeOrder(
            @RequestHeader("Authorization") String accessToken,
            @RequestBody OrderRequest request) {
        log.info("주문 요청: {} {} {}", request.getSymbol(), request.getOrderType(), request.getQuantity());
        return domesticStockService.placeOrder(accessToken, request)
                .map(ResponseEntity::ok)
                .doOnError(error -> log.error("주문 처리 실패", error));
    }
    
    @PutMapping("/orders/{orderId}")
    @Operation(summary = "주문 정정", description = "미체결 주문 가격/수량 정정")
    public Mono<ResponseEntity<OrderResponse>> modifyOrder(
            @RequestHeader("Authorization") String accessToken,
            @PathVariable String orderId,
            @RequestBody OrderModifyRequest request) {
        log.info("주문 정정 요청: {}", orderId);
        return domesticStockService.modifyOrder(accessToken, orderId, request)
                .map(ResponseEntity::ok);
    }
    
    @DeleteMapping("/orders/{orderId}")
    @Operation(summary = "주문 취소", description = "미체결 주문 취소")
    public Mono<ResponseEntity<OrderResponse>> cancelOrder(
            @RequestHeader("Authorization") String accessToken,
            @PathVariable String orderId,
            @RequestBody OrderCancelRequest request) {
        log.info("주문 취소 요청: {}", orderId);
        return domesticStockService.cancelOrder(accessToken, orderId, request)
                .map(ResponseEntity::ok);
    }
    
    // ========== 계좌 조회 API ==========
    
    @GetMapping("/account/balance")
    @Operation(summary = "계좌 잔고 조회", description = "예수금 및 주문가능금액 조회")
    public Mono<ResponseEntity<AccountBalanceResponse>> getAccountBalance(
            @RequestHeader("Authorization") String accessToken,
            @RequestParam String accountNumber) {
        log.info("계좌 잔고 조회: {}", accountNumber);
        return domesticStockService.getAccountBalance(accessToken, accountNumber)
                .map(ResponseEntity::ok);
    }
    
    @GetMapping("/account/positions")
    @Operation(summary = "보유 종목 조회", description = "계좌의 보유 종목 및 손익 조회")
    public Flux<PositionResponse> getPositions(
            @RequestHeader("Authorization") String accessToken,
            @RequestParam String accountNumber) {
        log.info("보유 종목 조회: {}", accountNumber);
        return domesticStockService.getPositions(accessToken, accountNumber);
    }
    
    @GetMapping("/account/orders")
    @Operation(summary = "주문 내역 조회", description = "당일 주문 내역 조회")
    public Flux<OrderHistoryResponse> getOrderHistory(
            @RequestHeader("Authorization") String accessToken,
            @RequestParam String accountNumber,
            @RequestParam(required = false) String orderStatus) {
        log.info("주문 내역 조회: {} - {}", accountNumber, orderStatus);
        return domesticStockService.getOrderHistory(accessToken, accountNumber, orderStatus);
    }
    
    // ========== 시세 조회 API ==========
    
    @GetMapping("/quotes/{symbol}")
    @Operation(summary = "현재가 조회", description = "종목의 현재가 및 호가 정보 조회")
    public Mono<ResponseEntity<StockQuoteResponse>> getQuote(
            @RequestHeader("Authorization") String accessToken,
            @PathVariable String symbol) {
        log.info("현재가 조회: {}", symbol);
        return domesticStockService.getQuote(accessToken, symbol)
                .map(ResponseEntity::ok);
    }
    
    @GetMapping("/quotes/{symbol}/orderbook")
    @Operation(summary = "호가 조회", description = "종목의 매수/매도 호가 조회")
    public Mono<ResponseEntity<OrderBookResponse>> getOrderBook(
            @RequestHeader("Authorization") String accessToken,
            @PathVariable String symbol) {
        log.info("호가 조회: {}", symbol);
        return domesticStockService.getOrderBook(accessToken, symbol)
                .map(ResponseEntity::ok);
    }
    
    @GetMapping("/quotes/{symbol}/daily")
    @Operation(summary = "일봉 조회", description = "종목의 일별 시세 조회")
    public Flux<DailyPriceResponse> getDailyPrices(
            @RequestHeader("Authorization") String accessToken,
            @PathVariable String symbol,
            @RequestParam(defaultValue = "30") int period) {
        log.info("일봉 조회: {} - {}일", symbol, period);
        return domesticStockService.getDailyPrices(accessToken, symbol, period);
    }
    
    // ========== 종목 정보 API ==========
    
    @GetMapping("/stocks/{symbol}")
    @Operation(summary = "종목 정보 조회", description = "종목 기본 정보 조회")
    public Mono<ResponseEntity<StockInfoResponse>> getStockInfo(
            @RequestHeader("Authorization") String accessToken,
            @PathVariable String symbol) {
        log.info("종목 정보 조회: {}", symbol);
        return domesticStockService.getStockInfo(accessToken, symbol)
                .map(ResponseEntity::ok);
    }
    
    @GetMapping("/stocks/search")
    @Operation(summary = "종목 검색", description = "종목명 또는 종목코드로 검색")
    public Flux<StockSearchResponse> searchStocks(
            @RequestHeader("Authorization") String accessToken,
            @RequestParam String keyword) {
        log.info("종목 검색: {}", keyword);
        return domesticStockService.searchStocks(accessToken, keyword);
    }
}