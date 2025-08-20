package com.quantum.api.kiwoom.service;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.order.*;
import com.quantum.api.kiwoom.dto.stock.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 국내주식 거래 서비스 (Reactive)
 * 자동매매 핵심 비즈니스 로직 처리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class DomesticStockService {

    private final KiwoomApiClient kiwoomApiClient;

    // ========== 주문 관련 서비스 ==========

    /**
     * 주식 매수/매도 주문 (Non-blocking)
     */
    public Mono<OrderResponse> placeOrder(String accessToken, OrderRequest request) {
        log.info("주문 처리 시작: {} {} {}주",
                request.getSymbol(), request.getOrderType(), request.getQuantity());

        // 주문 전 잔고 확인 후 주문 실행
        return validateOrderRequest(accessToken, request)
                .then(kiwoomApiClient.submitOrder(accessToken, request))
                .doOnNext(response -> {
                    if (response.isSuccess()) {
                        log.info("주문 성공: 주문번호 {}", response.getOrderId());
                    } else {
                        log.warn("주문 실패: {}", response.getMessage());
                    }
                })
                .onErrorReturn(OrderResponse.builder()
                        .success(false)
                        .message("주문 처리 실패")
                        .build());
    }

    /**
     * 주문 정정 (Non-blocking)
     */
    public Mono<OrderResponse> modifyOrder(String accessToken, String orderId, OrderModifyRequest request) {
        log.info("주문 정정 시작: {}", orderId);

        return kiwoomApiClient.modifyOrder(accessToken, orderId, request)
                .doOnNext(response -> {
                    if (response.isSuccess()) {
                        log.info("주문 정정 성공: {}", orderId);
                    } else {
                        log.warn("주문 정정 실패: {}", response.getMessage());
                    }
                })
                .onErrorReturn(OrderResponse.builder()
                        .orderId(orderId)
                        .success(false)
                        .message("주문 정정 실패")
                        .build());
    }

    /**
     * 주문 취소 (Non-blocking)
     */
    public Mono<OrderResponse> cancelOrder(String accessToken, String orderId, OrderCancelRequest request) {
        log.info("주문 취소 시작: {}", orderId);

        return kiwoomApiClient.cancelOrder(accessToken, orderId, request)
                .doOnNext(response -> {
                    if (response.isSuccess()) {
                        log.info("주문 취소 성공: {}", orderId);
                    } else {
                        log.warn("주문 취소 실패: {}", response.getMessage());
                    }
                })
                .onErrorReturn(OrderResponse.builder()
                        .orderId(orderId)
                        .success(false)
                        .message("주문 취소 실패")
                        .build());
    }

    // ========== 계좌 조회 서비스 ==========

    /**
     * 계좌 잔고 조회 (Non-blocking)
     */
    public Mono<AccountBalanceResponse> getAccountBalance(String accessToken, String accountNumber) {
        log.info("계좌 잔고 조회: {}", accountNumber);

        return kiwoomApiClient.getAccountBalance(accessToken, accountNumber)
                .doOnNext(balance -> log.debug("잔고 조회 완료: 예수금 {}", balance.getCashBalance()))
                .onErrorResume(error -> {
                    log.error("계좌 잔고 조회 실패", error);
                    return Mono.error(new RuntimeException("계좌 잔고 조회에 실패했습니다."));
                });
    }

    /**
     * 보유 종목 조회 (Non-blocking Stream)
     */
    public Flux<PositionResponse> getPositions(String accessToken, String accountNumber) {
        log.info("보유 종목 조회: {}", accountNumber);

        return kiwoomApiClient.getPositions(accessToken, accountNumber)
                .doOnNext(position -> log.debug("보유종목: {} {}주",
                        position.getSymbol(), position.getQuantity()))
                .onErrorResume(error -> {
                    log.error("보유 종목 조회 실패", error);
                    return Flux.error(new RuntimeException("보유 종목 조회에 실패했습니다."));
                });
    }

    /**
     * 주문 내역 조회 (Non-blocking Stream)
     */
    public Flux<OrderHistoryResponse> getOrderHistory(String accessToken, String accountNumber, String orderStatus) {
        log.info("주문 내역 조회: {} - {}", accountNumber, orderStatus);

        return kiwoomApiClient.getOrderHistory(accessToken, accountNumber, orderStatus)
                .doOnNext(order -> log.debug("주문: {} - {}",
                        order.getOrderId(), order.getOrderStatus()))
                .onErrorResume(error -> {
                    log.error("주문 내역 조회 실패", error);
                    return Flux.error(new RuntimeException("주문 내역 조회에 실패했습니다."));
                });
    }

    // ========== 시세 조회 서비스 ==========

    /**
     * 현재가 조회 (Non-blocking with Cache)
     */
    public Mono<StockQuoteResponse> getQuote(String accessToken, String symbol) {
        log.debug("현재가 조회: {}", symbol);

        return kiwoomApiClient.getStockQuote(accessToken, symbol)
                .cache() // 5초간 캐싱
                .doOnNext(quote -> log.debug("{} 현재가: {}",
                        symbol, quote.getCurrentPrice()))
                .onErrorResume(error -> {
                    log.error("현재가 조회 실패: {}", symbol, error);
                    return Mono.error(new RuntimeException("현재가 조회에 실패했습니다."));
                });
    }

    /**
     * 호가 조회 (Non-blocking)
     */
    public Mono<OrderBookResponse> getOrderBook(String accessToken, String symbol) {
        log.debug("호가 조회: {}", symbol);

        return kiwoomApiClient.getOrderBook(accessToken, symbol)
                .doOnNext(orderBook -> log.debug("{} 매도1호가: {}, 매수1호가: {}",
                        symbol,
                        orderBook.getAsks().isEmpty() ? "없음" : orderBook.getAsks().get(0).getPrice(),
                        orderBook.getBids().isEmpty() ? "없음" : orderBook.getBids().get(0).getPrice()))
                .onErrorResume(error -> {
                    log.error("호가 조회 실패: {}", symbol, error);
                    return Mono.error(new RuntimeException("호가 조회에 실패했습니다."));
                });
    }

    /**
     * 일봉 조회 (Non-blocking Stream)
     */
    public Flux<DailyPriceResponse> getDailyPrices(String accessToken, String symbol, int period) {
        log.debug("일봉 조회: {} - {}일", symbol, period);

        return kiwoomApiClient.getDailyPrices(accessToken, symbol, period)
                .doOnNext(price -> log.debug("{} 일봉: {} - {}",
                        symbol, price.getDate(), price.getClosePrice()))
                .onErrorResume(error -> {
                    log.error("일봉 조회 실패: {}", symbol, error);
                    return Flux.error(new RuntimeException("일봉 조회에 실패했습니다."));
                });
    }

    // ========== 종목 정보 서비스 ==========

    /**
     * 종목 정보 조회 (Non-blocking)
     */
    public Mono<StockInfoResponse> getStockInfo(String accessToken, String symbol) {
        log.info("종목 정보 조회: {}", symbol);

        return kiwoomApiClient.getStockInfo(accessToken, symbol)
                .doOnNext(info -> log.info("{} - {}",
                        info.getStockCode(), info.getStockName()))
                .onErrorResume(error -> {
                    log.error("종목 정보 조회 실패: {}", symbol, error);
                    return Mono.error(new RuntimeException("종목 정보 조회에 실패했습니다."));
                });
    }

    /**
     * 종목 검색 (Non-blocking Stream)
     */
    public Flux<StockSearchResponse> searchStocks(String accessToken, String keyword) {
        log.info("종목 검색: {}", keyword);

        return kiwoomApiClient.searchStocks(accessToken, keyword)
                .doOnNext(stock -> log.debug("검색결과: {} - {}",
                        stock.getSymbol(), stock.getStockName()))
                .onErrorResume(error -> {
                    log.error("종목 검색 실패: {}", keyword, error);
                    return Flux.error(new RuntimeException("종목 검색에 실패했습니다."));
                });
    }

    // ========== Private Methods ==========

    /**
     * 주문 요청 검증 (Reactive)
     */
    private Mono<Void> validateOrderRequest(String accessToken, OrderRequest request) {
        if (request.getOrderType() == OrderRequest.OrderType.BUY) {
            // 매수 시 주문가능금액 확인
            return getAccountBalance(accessToken, request.getAccountNumber())
                    .flatMap(balance -> {
                        var orderAmount = request.getPrice()
                                .multiply(new java.math.BigDecimal(request.getQuantity()));
                        if (balance.getAvailableCash().compareTo(orderAmount) < 0) {
                            return Mono.error(new IllegalArgumentException("주문가능금액이 부족합니다."));
                        }
                        return Mono.empty();
                    });
        } else if (request.getOrderType() == OrderRequest.OrderType.SELL) {
            // 매도 시 보유수량 확인
            return getPositions(accessToken, request.getAccountNumber())
                    .filter(p -> p.getSymbol().equals(request.getSymbol()))
                    .next()
                    .switchIfEmpty(Mono.error(new IllegalArgumentException("보유하지 않은 종목입니다.")))
                    .flatMap(position -> {
                        if (position.getTradableQuantity() < request.getQuantity()) {
                            return Mono.error(new IllegalArgumentException("매도가능수량이 부족합니다."));
                        }
                        return Mono.empty();
                    });
        }
        return Mono.empty();
    }
}
