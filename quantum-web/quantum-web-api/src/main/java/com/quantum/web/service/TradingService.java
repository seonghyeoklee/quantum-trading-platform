package com.quantum.web.service;

import com.quantum.trading.platform.query.service.OrderQueryService;
import com.quantum.trading.platform.query.service.PortfolioQueryService;
import com.quantum.trading.platform.shared.command.CancelOrderCommand;
import com.quantum.trading.platform.shared.command.CreateOrderCommand;
import com.quantum.trading.platform.shared.value.*;
import com.quantum.web.controller.TradingController.CreateOrderRequest;
import com.quantum.web.service.RiskManagementService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.messaging.responsetypes.ResponseTypes;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/**
 * Trading Service
 * 
 * CQRS/Event Sourcing 기반 거래 관련 비즈니스 로직 처리 서비스
 * - CommandGateway를 통한 도메인 Command 발행
 * - QueryGateway를 통한 Read Model 조회
 * - Event Sourcing 기반 주문 상태 관리
 * - 키움 API와의 실시간 연동
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TradingService {

    private final CommandGateway commandGateway;
    private final QueryGateway queryGateway;
    private final OrderQueryService orderQueryService;
    private final PortfolioQueryService portfolioQueryService;
    private final RiskManagementService riskManagementService;

    /**
     * 주문 생성 - CQRS Command 패턴 사용
     * 
     * @param request 주문 생성 요청
     * @return CompletableFuture<OrderResponse> 비동기 주문 생성 결과
     */
    public CompletableFuture<OrderResponse> createOrder(CreateOrderRequest request) {
        log.info("Creating order - portfolio: {}, symbol: {}, side: {}, quantity: {}", 
                request.portfolioId(), request.symbol(), request.side(), request.quantity());
        
        try {
            // 1. 주문 유효성 검증
            validateOrderRequest(request);
            
            // 1.1 도메인 Value Objects 생성 (리스크 검증용)
            UserId userId = extractUserIdFromContext();
            Symbol symbol = Symbol.of(request.symbol());
            OrderType orderType = OrderType.valueOf(request.type());
            OrderSide side = OrderSide.valueOf(request.side());
            Money price = request.price() != null ? Money.of(request.price()) : null;
            Quantity quantity = Quantity.of(request.quantity());
            PortfolioId portfolioId = PortfolioId.of(request.portfolioId());
            
            // 1.2 리스크 관리 검증
            RiskManagementService.RiskValidationResult riskResult = 
                    riskManagementService.validateOrder(userId, portfolioId, symbol, side, quantity, price, orderType);
            
            if (!riskResult.isValid()) {
                throw new TradingException("Risk validation failed: " + riskResult.getMessage());
            }
            
            log.info("✅ Risk validation passed: {} (level: {})", 
                    riskResult.getMessage(), riskResult.getRiskLevel());
            
            // 2. 주문 생성 준비
            OrderId orderId = OrderId.generate();
            
            // 3. CreateOrderCommand 생성 및 발행
            CreateOrderCommand command = new CreateOrderCommand(
                    orderId,
                    userId,
                    symbol,
                    orderType,
                    side,
                    price,
                    quantity
            );
            
            log.info("Sending CreateOrderCommand - orderId: {}", orderId.value());
            
            // 4. CommandGateway로 명령 전송 (Event Sourcing)
            return commandGateway.send(command)
                    .thenApply(result -> {
                        log.info("Order command processed successfully - orderId: {}", orderId.value());
                        
                        // 5. 응답 DTO 생성
                        return new OrderResponse(
                                orderId.value(),
                                request.portfolioId(),
                                request.symbol(),
                                request.side(),
                                request.type(),
                                request.quantity(),
                                request.price(),
                                request.stopPrice(),
                                OrderStatus.PENDING.name(),
                                0,
                                request.quantity(),
                                null, // averagePrice
                                null, // brokerOrderId
                                LocalDateTime.now(),
                                LocalDateTime.now()
                        );
                    })
                    .exceptionally(throwable -> {
                        log.error("Failed to create order - orderId: {}", orderId.value(), throwable);
                        throw new RuntimeException(new TradingException("주문 생성에 실패했습니다: " + throwable.getMessage(), throwable));
                    });
            
        } catch (Exception e) {
            log.error("Order validation failed", e);
            CompletableFuture<OrderResponse> failedFuture = new CompletableFuture<>();
            failedFuture.completeExceptionally(e);
            return failedFuture;
        }
    }

    /**
     * 주문 취소 - CQRS Command 패턴 사용
     * 
     * @param orderId 취소할 주문 ID
     * @return CompletableFuture<CancelOrderResponse> 비동기 주문 취소 결과
     */
    public CompletableFuture<CancelOrderResponse> cancelOrder(String orderId) {
        log.info("Cancelling order - orderId: {}", orderId);
        
        try {
            // 1. 주문 존재 여부 및 취소 가능 여부 확인 (Query Side)
            var orderOpt = orderQueryService.getOrderById(orderId);
            if (orderOpt.isEmpty()) {
                throw new IllegalArgumentException("주문을 찾을 수 없습니다: " + orderId);
            }
            
            var order = orderOpt.get();
            if (!order.getStatus().isCancellable()) {
                throw new IllegalStateException("현재 상태에서는 주문을 취소할 수 없습니다: " + order.getStatus());
            }
            
            // 2. CancelOrderCommand 생성 및 발행
            CancelOrderCommand command = new CancelOrderCommand(
                    OrderId.of(orderId),
                    "사용자 요청에 의한 주문 취소"
            );
            
            log.info("Sending CancelOrderCommand - orderId: {}", orderId);
            
            // 3. CommandGateway로 명령 전송
            return commandGateway.send(command)
                    .thenApply(result -> {
                        log.info("Order cancel command processed successfully - orderId: {}", orderId);
                        
                        return new CancelOrderResponse(
                                orderId,
                                OrderStatus.CANCELLED.name(),
                                LocalDateTime.now(),
                                "주문이 성공적으로 취소되었습니다"
                        );
                    })
                    .exceptionally(throwable -> {
                        log.error("Failed to cancel order - orderId: {}", orderId, throwable);
                        throw new TradingException("주문 취소에 실패했습니다: " + throwable.getMessage(), throwable);
                    });
            
        } catch (Exception e) {
            log.error("Order cancellation failed for orderId: {}", orderId, e);
            CompletableFuture<CancelOrderResponse> failedFuture = new CompletableFuture<>();
            failedFuture.completeExceptionally(e);
            return failedFuture;
        }
    }

    /**
     * 주문 목록 조회 - Query Side 사용
     * 
     * @param portfolioId 포트폴리오 ID
     * @param status 주문 상태 필터
     * @param page 페이지 번호
     * @param size 페이지 크기
     * @return 주문 목록과 페이징 정보
     */
    public PageResponse<OrderResponse> getOrders(String portfolioId, String status, int page, int size) {
        log.debug("Getting orders - portfolio: {}, status: {}, page: {}, size: {}", 
                 portfolioId, status, page, size);
        
        try {
            // 1. 페이징 정보 생성
            Pageable pageable = PageRequest.of(page, size);
            
            // 2. Query Service를 통한 주문 목록 조회
            var orderPage = orderQueryService.getOrdersByPortfolioId(
                    portfolioId, 
                    status != null ? OrderStatus.valueOf(status) : null, 
                    pageable);
            
            // 3. DTO 변환
            var orderResponses = orderPage.getContent().stream()
                    .map(order -> new OrderResponse(
                            order.getOrderId(),
                            order.getPortfolioId(),
                            order.getSymbol(),
                            order.getSide().name(),
                            order.getOrderType().name(),
                            order.getQuantity(),
                            order.getPrice(),
                            order.getStopPrice(),
                            order.getStatus().name(),
                            order.getFilledQuantity(),
                            order.getRemainingQuantity(),
                            order.getAveragePrice(),
                            order.getBrokerOrderId(),
                            order.getCreatedAt(),
                            order.getUpdatedAt()
                    ))
                    .toList();
            
            return PageResponse.<OrderResponse>builder()
                    .content(orderResponses)
                    .page(page)
                    .size(size)
                    .totalElements(orderPage.getTotalElements())
                    .totalPages(orderPage.getTotalPages())
                    .build();
            
        } catch (Exception e) {
            log.error("Failed to get orders for portfolio: {}", portfolioId, e);
            throw new TradingException("주문 목록 조회에 실패했습니다: " + e.getMessage(), e);
        }
    }

    /**
     * 주문 상세 조회 - Query Side 사용
     * 
     * @param orderId 조회할 주문 ID
     * @return 주문 상세 정보 또는 null
     */
    public OrderResponse getOrder(String orderId) {
        log.debug("Getting order detail - orderId: {}", orderId);
        
        try {
            // Query Service를 통한 주문 상세 조회
            var orderOpt = orderQueryService.getOrderById(orderId);
            
            if (orderOpt.isEmpty()) {
                log.warn("Order not found - orderId: {}", orderId);
                return null;
            }
            
            var order = orderOpt.get();
            
            // DTO 변환
            return new OrderResponse(
                    order.getOrderId(),
                    order.getPortfolioId(),
                    order.getSymbol(),
                    order.getSide().name(),
                    order.getOrderType().name(),
                    order.getQuantity(),
                    order.getPrice(),
                    order.getStopPrice(),
                    order.getStatus().name(),
                    order.getFilledQuantity(),
                    order.getRemainingQuantity(),
                    order.getAveragePrice(),
                    order.getBrokerOrderId(),
                    order.getCreatedAt(),
                    order.getUpdatedAt()
            );
            
        } catch (Exception e) {
            log.error("Failed to get order - orderId: {}", orderId, e);
            throw new TradingException("주문 상세 조회에 실패했습니다: " + e.getMessage(), e);
        }
    }

    /**
     * 거래 내역 조회 - Query Side 사용
     * 
     * @param portfolioId 포트폴리오 ID
     * @param symbol 종목 코드 필터
     * @param fromDate 시작 날짜
     * @param toDate 종료 날짜
     * @param page 페이지 번호
     * @param size 페이지 크기
     * @return 거래 내역 목록과 페이징 정보
     */
    public PageResponse<TradeResponse> getTrades(String portfolioId, String symbol, 
                                               String fromDate, String toDate, int page, int size) {
        log.debug("Getting trades - portfolio: {}, symbol: {}, from: {}, to: {}", 
                 portfolioId, symbol, fromDate, toDate);
        
        try {
            // 1. 페이징 정보 생성
            Pageable pageable = PageRequest.of(page, size);
            
            // 2. Query Service를 통한 거래 내역 조회
            var tradePage = orderQueryService.getTradesByPortfolioId(
                    portfolioId, symbol, fromDate, toDate, pageable);
            
            // 3. DTO 변환
            var tradeResponses = tradePage.getContent().stream()
                    .map(trade -> TradeResponse.builder()
                            .tradeId(trade.getTradeId())
                            .orderId(trade.getOrderId())
                            .portfolioId(trade.getPortfolioId())
                            .symbol(trade.getSymbol())
                            .side(trade.getSide().name())
                            .quantity(trade.getQuantity())
                            .price(trade.getPrice())
                            .amount(trade.getAmount())
                            .executedAt(trade.getExecutedAt())
                            .build())
                    .toList();
            
            return PageResponse.<TradeResponse>builder()
                    .content(tradeResponses)
                    .page(page)
                    .size(size)
                    .totalElements(tradePage.getTotalElements())
                    .totalPages(tradePage.getTotalPages())
                    .build();
            
        } catch (Exception e) {
            log.error("Failed to get trades for portfolio: {}", portfolioId, e);
            throw new TradingException("거래 내역 조회에 실패했습니다: " + e.getMessage(), e);
        }
    }

    /**
     * 주문 요청 유효성 검증
     */
    private void validateOrderRequest(CreateOrderRequest request) {
        // 1. 기본 필드 검증
        if (request.portfolioId() == null || request.portfolioId().trim().isEmpty()) {
            throw new IllegalArgumentException("포트폴리오 ID는 필수입니다");
        }
        
        if (request.symbol() == null || !request.symbol().matches("^[A-Z0-9]{6}$")) {
            throw new IllegalArgumentException("유효하지 않은 종목 코드입니다");
        }
        
        if (request.quantity() <= 0) {
            throw new IllegalArgumentException("주문 수량은 0보다 커야 합니다");
        }
        
        // 2. 주문 유형별 필수 필드 검증
        OrderType orderType = OrderType.valueOf(request.type());
        
        if (orderType.requiresPrice()) {
            if (request.price() == null || request.price().compareTo(BigDecimal.ZERO) <= 0) {
                throw new IllegalArgumentException("지정가 주문은 유효한 가격이 필요합니다");
            }
        }
        
        // 한국 주식시장에서는 일반적으로 STOP 주문을 지원하지 않으므로 해당 검증 로직 제거
        
        // 3. 포트폴리오 존재 여부 확인
        if (!portfolioQueryService.portfolioExists(request.portfolioId())) {
            throw new IllegalArgumentException("존재하지 않는 포트폴리오입니다: " + request.portfolioId());
        }
        
        // 4. 매도 주문 시 보유 수량 확인
        if ("SELL".equals(request.side())) {
            validateSellOrderQuantity(request);
        }
        
        log.debug("Order request validation passed - symbol: {}, type: {}, quantity: {}", 
                 request.symbol(), request.type(), request.quantity());
    }

    /**
     * 매도 주문 수량 검증
     */
    private void validateSellOrderQuantity(CreateOrderRequest request) {
        try {
            var positionOpt = portfolioQueryService.getPosition(request.portfolioId(), request.symbol());
            
            if (positionOpt.isEmpty()) {
                throw new IllegalArgumentException("보유하지 않은 종목입니다: " + request.symbol());
            }
            
            var position = positionOpt.get();
            if (position.getQuantity() < request.quantity()) {
                throw new IllegalArgumentException(
                        String.format("보유 수량(%d)이 매도 요청 수량(%d)보다 적습니다", 
                                position.getQuantity(), request.quantity()));
            }
            
        } catch (Exception e) {
            log.error("Failed to validate sell order quantity", e);
            throw new IllegalArgumentException("매도 주문 수량 검증에 실패했습니다: " + e.getMessage());
        }
    }

    /**
     * JWT 토큰에서 사용자 ID 추출
     */
    private UserId extractUserIdFromContext() {
        // TODO: Spring Security Context에서 사용자 ID 추출
        // 현재는 임시로 하드코딩
        return UserId.of("USER-CURRENT");
    }

    /**
     * 거래 관련 예외 클래스
     */
    public static class TradingException extends RuntimeException {
        public TradingException(String message) {
            super(message);
        }
        
        public TradingException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    // Response DTOs
    @lombok.Builder
    public record OrderResponse(
            String orderId,
            String portfolioId,
            String symbol,
            String side,
            String type,
            Integer quantity,
            BigDecimal price,
            BigDecimal stopPrice,
            String status,
            Integer filledQuantity,
            Integer remainingQuantity,
            BigDecimal averagePrice,
            String brokerOrderId,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {}

    @lombok.Builder
    public record CancelOrderResponse(
            String orderId,
            String status,
            LocalDateTime cancelledAt,
            String message
    ) {}

    @lombok.Builder
    public record TradeResponse(
            String tradeId,
            String orderId,
            String portfolioId,
            String symbol,
            String side,
            Integer quantity,
            BigDecimal price,
            BigDecimal amount,
            LocalDateTime executedAt
    ) {}

    @lombok.Builder
    public record PageResponse<T>(
            List<T> content,
            int page,
            int size,
            long totalElements,
            int totalPages
    ) {}
}