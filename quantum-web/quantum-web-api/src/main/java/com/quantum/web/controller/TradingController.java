package com.quantum.web.controller;

import com.quantum.web.dto.ApiResponse;
import com.quantum.web.service.TradingService;
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
@RequestMapping("/orders")
@RequiredArgsConstructor
@Tag(name = "Trading", description = "거래 API")
public class TradingController {

    private final TradingService tradingService;

    @Operation(
        summary = "주문 생성",
        description = "새로운 주문을 생성합니다."
    )
    @PostMapping
    public ResponseEntity<ApiResponse<Object>> createOrder(
            @Valid @RequestBody CreateOrderRequest request
    ) {
        log.info("Order creation requested - portfolio: {}, symbol: {}, side: {}, quantity: {}",
                request.portfolioId(), request.symbol(), request.side(), request.quantity());

        try {
            var orderResponse = tradingService.createOrder(request);

            return ResponseEntity.ok(ApiResponse.success(orderResponse,
                String.format("주문 생성 완료 - %s %s %s", request.symbol(), request.side(), request.quantity())));

        } catch (IllegalArgumentException e) {
            log.warn("Invalid order request: {}", e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error(e.getMessage(), "INVALID_ORDER"));

        } catch (Exception e) {
            log.error("Failed to create order", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("주문 생성 중 오류가 발생했습니다", "ORDER_CREATE_ERROR"));
        }
    }

    @Operation(
        summary = "주문 취소",
        description = "기존 주문을 취소합니다."
    )
    @DeleteMapping("/{orderId}")
    public ResponseEntity<ApiResponse<Object>> cancelOrder(
            @Parameter(description = "주문 ID", example = "ORDER-123456")
            @PathVariable String orderId
    ) {
        log.info("Order cancellation requested - orderId: {}", orderId);

        try {
            var cancelResponse = tradingService.cancelOrder(orderId);

            return ResponseEntity.ok(ApiResponse.success(cancelResponse,
                String.format("주문 취소 완료 - %s", orderId)));

        } catch (IllegalArgumentException e) {
            log.warn("Invalid cancel request for orderId {}: {}", orderId, e.getMessage());
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error(e.getMessage(), "INVALID_CANCEL"));

        } catch (Exception e) {
            log.error("Failed to cancel order: {}", orderId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("주문 취소 중 오류가 발생했습니다", "ORDER_CANCEL_ERROR"));
        }
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
