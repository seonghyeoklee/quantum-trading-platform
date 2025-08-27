package com.quantum.web.controller;

import com.quantum.web.dto.ApiResponse;
import com.quantum.web.service.TradingService;
import com.quantum.web.service.TradingService.CancelOrderResponse;
import com.quantum.web.service.TradingService.OrderResponse;
import com.quantum.trading.platform.query.service.TradeQueryService;
import com.quantum.trading.platform.query.view.TradeView;
import com.quantum.trading.platform.shared.value.OrderSide;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.concurrent.CompletableFuture;
import com.quantum.web.service.TradingService.TradingException;
import org.springframework.data.domain.PageRequest;

/**
 * Trading Controller
 *
 * 거래 관련 API를 제공하는 컨트롤러
 * - 주문 생성/취소/조회
 * - 주문 상태 모니터링
 * - 거래 내역 조회
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
@Tag(name = "Trading", description = "거래 API")
public class TradingController {

    private final TradingService tradingService;
    private final TradeQueryService tradeQueryService;

    @Operation(
        summary = "주문 생성",
        description = "새로운 주문을 생성합니다."
    )
    @PostMapping
    public CompletableFuture<ResponseEntity<ApiResponse<OrderResponse>>> createOrder(
            @Valid @RequestBody CreateOrderRequest request
    ) {
        log.info("Order creation requested - portfolio: {}, symbol: {}, side: {}, quantity: {}",
                request.portfolioId(), request.symbol(), request.side(), request.quantity());

        return tradingService.createOrder(request)
                .thenApply(orderResponse -> {
                    log.info("Order created successfully - orderId: {}", orderResponse.orderId());
                    return ResponseEntity.ok(ApiResponse.success(orderResponse,
                        String.format("주문 생성 완료 - %s %s %s", request.symbol(), request.side(), request.quantity())));
                })
                .exceptionally(throwable -> {
                    Throwable cause = throwable.getCause() != null ? throwable.getCause() : throwable;

                    if (cause instanceof IllegalArgumentException || cause instanceof TradingService.TradingException) {
                        log.warn("Invalid order request: {}", cause.getMessage());
                        return ResponseEntity.badRequest()
                                .body(ApiResponse.<TradingService.OrderResponse>error(cause.getMessage(), "INVALID_ORDER"));
                    }

                    log.error("Failed to create order", cause);
                    return ResponseEntity.internalServerError()
                            .body(ApiResponse.<TradingService.OrderResponse>error("주문 생성 중 오류가 발생했습니다", "ORDER_CREATE_ERROR"));
                });
    }

    @Operation(
        summary = "주문 취소",
        description = "기존 주문을 취소합니다."
    )
    @DeleteMapping("/{orderId}")
    public CompletableFuture<ResponseEntity<ApiResponse<CancelOrderResponse>>> cancelOrder(
            @Parameter(description = "주문 ID", example = "ORDER-123456")
            @PathVariable String orderId
    ) {
        log.info("Order cancellation requested - orderId: {}", orderId);

        return tradingService.cancelOrder(orderId)
                .thenApply(cancelResponse -> {
                    log.info("Order cancelled successfully - orderId: {}", orderId);
                    return ResponseEntity.ok(ApiResponse.success(cancelResponse,
                        String.format("주문 취소 완료 - %s", orderId)));
                })
                .exceptionally(throwable -> {
                    Throwable cause = throwable.getCause() != null ? throwable.getCause() : throwable;

                    if (cause instanceof IllegalArgumentException || cause instanceof IllegalStateException) {
                        log.warn("Invalid cancel request for orderId {}: {}", orderId, cause.getMessage());
                        return ResponseEntity.badRequest()
                                .body(ApiResponse.<TradingService.CancelOrderResponse>error(cause.getMessage(), "INVALID_CANCEL"));
                    }

                    log.error("Failed to cancel order: {}", orderId, cause);
                    return ResponseEntity.internalServerError()
                            .body(ApiResponse.<TradingService.CancelOrderResponse>error("주문 취소 중 오류가 발생했습니다", "ORDER_CANCEL_ERROR"));
                });
    }

    @Operation(
        summary = "주문 목록 조회",
        description = "포트폴리오의 주문 목록을 조회합니다."
    )
    @GetMapping
    public ResponseEntity<ApiResponse<Object>> getOrders(
            @Parameter(description = "포트폴리오 ID", example = "PORTFOLIO-123")
            @RequestParam String portfolioId,

            @Parameter(description = "주문 상태 필터", example = "PENDING")
            @RequestParam(required = false)
            @Pattern(regexp = "^(PENDING|SUBMITTED|FILLED|CANCELLED|REJECTED)$", message = "유효하지 않은 주문 상태입니다")
            String status,

            @Parameter(description = "페이지 번호 (0부터 시작)", example = "0")
            @RequestParam(defaultValue = "0")
            @Min(value = 0, message = "페이지 번호는 0 이상이어야 합니다")
            int page,

            @Parameter(description = "페이지 크기", example = "20")
            @RequestParam(defaultValue = "20")
            @Min(value = 1, message = "페이지 크기는 1 이상이어야 합니다")
            @Max(value = 100, message = "페이지 크기는 100 이하여야 합니다")
            int size
    ) {
        log.debug("Orders requested - portfolio: {}, status: {}, page: {}, size: {}",
                 portfolioId, status, page, size);

        try {
            var orders = tradingService.getOrders(portfolioId, status, page, size);

            return ResponseEntity.ok(ApiResponse.success(orders,
                String.format("주문 목록 조회 완료 - %s", portfolioId)));

        } catch (Exception e) {
            log.error("Failed to get orders for portfolio: {}", portfolioId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("주문 목록 조회 중 오류가 발생했습니다", "ORDERS_GET_ERROR"));
        }
    }

    @Operation(
        summary = "주문 상세 조회",
        description = "특정 주문의 상세 정보를 조회합니다."
    )
    @GetMapping("/{orderId}")
    public ResponseEntity<ApiResponse<Object>> getOrder(
            @Parameter(description = "주문 ID", example = "ORDER-123456")
            @PathVariable String orderId
    ) {
        log.debug("Order detail requested - orderId: {}", orderId);

        try {
            var order = tradingService.getOrder(orderId);

            if (order == null) {
                return ResponseEntity.notFound().build();
            }

            return ResponseEntity.ok(ApiResponse.success(order,
                String.format("주문 상세 조회 완료 - %s", orderId)));

        } catch (Exception e) {
            log.error("Failed to get order: {}", orderId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("주문 상세 조회 중 오류가 발생했습니다", "ORDER_GET_ERROR"));
        }
    }

    @Operation(
        summary = "거래 내역 조회",
        description = "포트폴리오의 체결된 거래 내역을 조회합니다."
    )
    @GetMapping("/trades")
    public ResponseEntity<ApiResponse<Object>> getTrades(
            @Parameter(description = "포트폴리오 ID", example = "PORTFOLIO-123")
            @RequestParam String portfolioId,

            @Parameter(description = "종목 코드 필터", example = "005930")
            @RequestParam(required = false) String symbol,

            @Parameter(description = "시작 날짜 (YYYY-MM-DD)", example = "2024-01-01")
            @RequestParam(required = false)
            @Pattern(regexp = "^\\d{4}-\\d{2}-\\d{2}$", message = "날짜 형식은 YYYY-MM-DD여야 합니다")
            String fromDate,

            @Parameter(description = "종료 날짜 (YYYY-MM-DD)", example = "2024-12-31")
            @RequestParam(required = false)
            @Pattern(regexp = "^\\d{4}-\\d{2}-\\d{2}$", message = "날짜 형식은 YYYY-MM-DD여야 합니다")
            String toDate,

            @Parameter(description = "페이지 번호", example = "0")
            @RequestParam(defaultValue = "0")
            @Min(value = 0, message = "페이지 번호는 0 이상이어야 합니다")
            int page,

            @Parameter(description = "페이지 크기", example = "20")
            @RequestParam(defaultValue = "20")
            @Min(value = 1, message = "페이지 크기는 1 이상이어야 합니다")
            @Max(value = 100, message = "페이지 크기는 100 이하여야 합니다")
            int size
    ) {
        log.debug("Trades requested - portfolio: {}, symbol: {}, from: {}, to: {}",
                 portfolioId, symbol, fromDate, toDate);

        try {
            var trades = tradingService.getTrades(portfolioId, symbol, fromDate, toDate, page, size);

            return ResponseEntity.ok(ApiResponse.success(trades,
                String.format("거래 내역 조회 완료 - %s", portfolioId)));

        } catch (Exception e) {
            log.error("Failed to get trades for portfolio: {}", portfolioId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("거래 내역 조회 중 오류가 발생했습니다", "TRADES_GET_ERROR"));
        }
    }

    // ===============================================
    // 새로운 거래 이력 API (TradeView 기반)
    // ===============================================

    @Operation(
        summary = "사용자별 거래 이력 조회",
        description = "사용자의 전체 거래 이력을 페이징하여 조회합니다."
    )
    @GetMapping("/history")
    public ResponseEntity<ApiResponse<Object>> getUserTradeHistory(
            @Parameter(description = "사용자 ID", example = "USER-123")
            @RequestParam String userId,

            @Parameter(description = "페이지 번호", example = "0")
            @RequestParam(defaultValue = "0")
            @Min(value = 0, message = "페이지 번호는 0 이상이어야 합니다")
            int page,

            @Parameter(description = "페이지 크기", example = "20")
            @RequestParam(defaultValue = "20")
            @Min(value = 1, message = "페이지 크기는 1 이상이어야 합니다")
            @Max(value = 100, message = "페이지 크기는 100 이하여야 합니다")
            int size
    ) {
        log.debug("User trade history requested - userId: {}, page: {}, size: {}", userId, page, size);

        try {
            var tradePage = tradeQueryService.getUserTrades(userId, 
                org.springframework.data.domain.PageRequest.of(page, size));
            return ResponseEntity.ok(ApiResponse.success(tradePage,
                String.format("사용자 거래 이력 조회 완료 - 총 %d개", tradePage.getTotalElements())));

        } catch (Exception e) {
            log.error("Failed to get user trade history: {}", userId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("거래 이력 조회 중 오류가 발생했습니다", "TRADE_HISTORY_ERROR"));
        }
    }

    @Operation(
        summary = "거래 통계 요약",
        description = "사용자의 전체 거래 통계를 조회합니다."
    )
    @GetMapping("/statistics/{userId}")
    public ResponseEntity<ApiResponse<TradeQueryService.TradingSummary>> getTradingStatistics(
            @Parameter(description = "사용자 ID", example = "USER-123")
            @PathVariable String userId
    ) {
        log.debug("Trading statistics requested - userId: {}", userId);

        try {
            var summary = tradeQueryService.getUserTradingSummary(userId);
            return ResponseEntity.ok(ApiResponse.success(summary, "거래 통계 조회 완료"));

        } catch (Exception e) {
            log.error("Failed to get trading statistics: {}", userId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("거래 통계 조회 중 오류가 발생했습니다", "TRADING_STATISTICS_ERROR"));
        }
    }

    @Operation(
        summary = "오늘 거래 이력 조회",
        description = "사용자의 오늘 거래 이력을 조회합니다."
    )
    @GetMapping("/history/{userId}/today")
    public ResponseEntity<ApiResponse<java.util.List<TradeView>>> getTodayTrades(
            @Parameter(description = "사용자 ID", example = "USER-123")
            @PathVariable String userId
    ) {
        log.debug("Today trades requested - userId: {}", userId);

        try {
            var todayTrades = tradeQueryService.getTodayTrades(userId);
            return ResponseEntity.ok(ApiResponse.success(todayTrades,
                String.format("오늘 거래 이력 조회 완료 - 총 %d개", todayTrades.size())));

        } catch (Exception e) {
            log.error("Failed to get today trades: {}", userId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("오늘 거래 이력 조회 중 오류가 발생했습니다", "TODAY_TRADES_ERROR"));
        }
    }

    // Request DTO
    public record CreateOrderRequest(
            @NotBlank(message = "포트폴리오 ID는 필수입니다")
            String portfolioId,

            @NotBlank(message = "종목 코드는 필수입니다")
            @Pattern(regexp = "^[A-Z0-9]{6}$", message = "종목 코드는 6자리 영숫자여야 합니다")
            String symbol,

            @NotNull(message = "주문 방향은 필수입니다")
            @Pattern(regexp = "^(BUY|SELL)$", message = "주문 방향은 BUY 또는 SELL이어야 합니다")
            String side,

            @NotNull(message = "주문 유형은 필수입니다")
            @Pattern(regexp = "^(MARKET|LIMIT|STOP|STOP_LIMIT)$", message = "지원되지 않는 주문 유형입니다")
            String type,

            @NotNull(message = "수량은 필수입니다")
            @Min(value = 1, message = "수량은 1 이상이어야 합니다")
            Integer quantity,

            @DecimalMin(value = "0.01", message = "가격은 0.01 이상이어야 합니다")
            BigDecimal price,

            @DecimalMin(value = "0.01", message = "손절가는 0.01 이상이어야 합니다")
            BigDecimal stopPrice
    ) {}
}
