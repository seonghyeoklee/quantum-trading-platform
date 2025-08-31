package com.quantum.web.service;

import com.quantum.trading.platform.shared.event.OrderCreatedEvent;
import com.quantum.trading.platform.shared.event.OrderExecutedEvent;
import com.quantum.trading.platform.shared.event.OrderRejectedEvent;
import com.quantum.trading.platform.shared.event.OrderStatusChangedEvent;
import com.quantum.trading.platform.shared.value.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.modelling.command.AggregateLifecycle;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * 주문 실행 서비스
 * 
 * CQRS Event Handler에서 호출되어 키움증권 API로 실제 주문을 전송하는 서비스
 * - OrderCreatedEvent 처리
 * - 키움증권 API 호출 (kt10000, kt10001)
 * - 주문 결과 처리 및 Event 발행
 * - 실시간 주문 상태 업데이트
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderExecutionService {
    
    private final CommandGateway commandGateway;
    private final KiwoomApiService kiwoomApiService;
    private final RestTemplate restTemplate = new RestTemplate();
    
    @Value("${kiwoom.adapter.base-url:http://localhost:10201}")
    private String kiwoomAdapterBaseUrl;
    
    @Value("${trading.execution.enabled:true}")
    private boolean executionEnabled;
    
    @Value("${trading.execution.simulate:false}")
    private boolean simulateExecution = false;
    
    /**
     * 주문 생성 이벤트 처리 - 키움증권 API로 주문 제출
     * 
     * @param orderCreatedEvent 주문 생성 이벤트
     * @return CompletableFuture<OrderExecutionResult> 비동기 실행 결과
     */
    public CompletableFuture<OrderExecutionResult> executeOrder(OrderCreatedEvent orderCreatedEvent) {
        log.info("Processing order execution - orderId: {}, symbol: {}, side: {}, quantity: {}", 
                orderCreatedEvent.orderId().value(), 
                orderCreatedEvent.symbol().value(),
                orderCreatedEvent.side(),
                orderCreatedEvent.quantity().value());
        
        if (!executionEnabled) {
            log.warn("Order execution is disabled - orderId: {}", orderCreatedEvent.orderId().value());
            return CompletableFuture.completedFuture(
                OrderExecutionResult.rejected("Order execution is disabled"));
        }
        
        return executeRealOrder(orderCreatedEvent);
    }
    
    /**
     * 실제 키움증권 API를 통한 주문 실행
     */
    private CompletableFuture<OrderExecutionResult> executeRealOrder(OrderCreatedEvent event) {
        log.info("Executing real order via Kiwoom API - orderId: {}", event.orderId().value());
        
        try {
            // 1. 주문 데이터 준비
            Map<String, Object> orderData = prepareKiwoomOrderData(event);
            
            // 2. 키움 API 엔드포인트 결정
            String endpoint = determineKiwoomEndpoint(event.side());
            String url = kiwoomAdapterBaseUrl + "/api/" + endpoint;
            
            log.info("Calling Kiwoom API - URL: {}, orderId: {}", url, event.orderId().value());
            
            // 3. HTTP 요청 헤더 설정
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(orderData, headers);
            
            // 4. 키움 API 호출 (비동기)
            return CompletableFuture.supplyAsync(() -> {
                try {
                    ResponseEntity<Map> response = restTemplate.exchange(
                            url, HttpMethod.POST, requestEntity, Map.class);
                    
                    return processKiwoomResponse(event, response);
                    
                } catch (Exception e) {
                    log.error("Kiwoom API call failed - orderId: {}", event.orderId().value(), e);
                    return OrderExecutionResult.rejected("Kiwoom API call failed: " + e.getMessage());
                }
            });
            
        } catch (Exception e) {
            log.error("Failed to prepare order execution - orderId: {}", event.orderId().value(), e);
            CompletableFuture<OrderExecutionResult> failedFuture = new CompletableFuture<>();
            failedFuture.complete(OrderExecutionResult.rejected("Failed to prepare order: " + e.getMessage()));
            return failedFuture;
        }
    }
    
    /**
     * 키움 API 응답 처리
     */
    private OrderExecutionResult processKiwoomResponse(OrderCreatedEvent event, ResponseEntity<Map> response) {
        try {
            Map<String, Object> responseBody = response.getBody();
            
            if (responseBody == null) {
                return OrderExecutionResult.rejected("Empty response from Kiwoom API");
            }
            
            // HTTP 상태 코드 확인
            if (!response.getStatusCode().is2xxSuccessful()) {
                String errorMessage = (String) responseBody.getOrDefault("message", "Unknown error");
                log.error("Kiwoom API returned error - orderId: {}, status: {}, message: {}", 
                         event.orderId().value(), response.getStatusCode(), errorMessage);
                return OrderExecutionResult.rejected("Kiwoom API error: " + errorMessage);
            }
            
            // 키움 API 응답 구조 파싱
            Integer code = (Integer) responseBody.get("Code");
            Map<String, Object> body = (Map<String, Object>) responseBody.get("Body");
            
            if (code == null || code != 200) {
                String errorMsg = body != null ? (String) body.get("msg1") : "Unknown error";
                log.error("Kiwoom order failed - orderId: {}, code: {}, message: {}", 
                         event.orderId().value(), code, errorMsg);
                return OrderExecutionResult.rejected("Kiwoom order rejected: " + errorMsg);
            }
            
            // 성공 시 브로커 주문 ID 추출
            String brokerOrderId = body != null ? (String) body.get("ord_no") : null;
            
            log.info("Kiwoom order submitted successfully - orderId: {}, brokerOrderId: {}", 
                    event.orderId().value(), brokerOrderId);
            
            return OrderExecutionResult.submitted(brokerOrderId);
            
        } catch (Exception e) {
            log.error("Failed to process Kiwoom response - orderId: {}", event.orderId().value(), e);
            return OrderExecutionResult.rejected("Failed to process response: " + e.getMessage());
        }
    }
    
    /**
     * 키움 API용 주문 데이터 준비
     */
    private Map<String, Object> prepareKiwoomOrderData(OrderCreatedEvent event) {
        Map<String, Object> data = new HashMap<>();
        
        // 키움 API 스펙에 맞는 데이터 구조
        data.put("dmst_stex_tp", "KRX"); // 국내거래소구분 (한국거래소)
        data.put("stk_cd", event.symbol().value()); // 종목코드
        data.put("ord_qty", String.valueOf(event.quantity().value())); // 주문수량
        
        // 주문 유형에 따른 가격 설정
        if (event.orderType() == OrderType.MARKET) {
            data.put("ord_uv", ""); // 시장가는 빈 문자열
            data.put("trde_tp", "3"); // 시장가 매매구분
        } else if (event.orderType() == OrderType.LIMIT) {
            data.put("ord_uv", event.price() != null ? event.price().amount().toString() : "");
            data.put("trde_tp", "0"); // 보통 매매구분
        } else {
            // 기타 주문 유형들 (STOP, STOP_LIMIT 등)
            data.put("ord_uv", event.price() != null ? event.price().amount().toString() : "");
            data.put("trde_tp", "5"); // 조건부지정가
        }
        
        data.put("cond_uv", ""); // 조건단가 (현재는 미사용)
        
        Map<String, Object> request = new HashMap<>();
        request.put("data", data);
        request.put("cont_yn", "N");
        request.put("next_key", "");
        
        return request;
    }
    
    /**
     * 매매 방향에 따른 키움 API 엔드포인트 결정
     */
    private String determineKiwoomEndpoint(OrderSide side) {
        return switch (side) {
            case BUY -> "fn_kt10000";  // 매수 주문
            case SELL -> "fn_kt10001"; // 매도 주문
        };
    }
    
    
    /**
     * 주문 취소 실행
     * 
     * @param orderId 취소할 주문 ID
     * @param brokerOrderId 브로커 주문 ID
     * @return CompletableFuture<OrderExecutionResult> 비동기 취소 결과
     */
    public CompletableFuture<OrderExecutionResult> cancelOrder(OrderId orderId, String brokerOrderId) {
        log.info("Processing order cancellation - orderId: {}, brokerOrderId: {}", 
                orderId.value(), brokerOrderId);
        
        if (!executionEnabled) {
            return CompletableFuture.completedFuture(
                OrderExecutionResult.rejected("Order execution is disabled"));
        }
        
        return executeRealCancel(orderId, brokerOrderId);
    }
    
    /**
     * 실제 키움증권 API를 통한 주문 취소
     */
    private CompletableFuture<OrderExecutionResult> executeRealCancel(OrderId orderId, String brokerOrderId) {
        log.info("Executing real order cancel via Kiwoom API - orderId: {}, brokerOrderId: {}", 
                orderId.value(), brokerOrderId);
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 키움 취소 API (kt10003) 호출 데이터 준비
                Map<String, Object> cancelData = new HashMap<>();
                cancelData.put("ord_no", brokerOrderId);
                // TODO: 추가 취소 파라미터들 설정
                
                Map<String, Object> request = new HashMap<>();
                request.put("data", cancelData);
                
                String url = kiwoomAdapterBaseUrl + "/api/fn_kt10003";
                
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                
                HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(request, headers);
                
                ResponseEntity<Map> response = restTemplate.exchange(
                        url, HttpMethod.POST, requestEntity, Map.class);
                
                return processCancelResponse(orderId, response);
                
            } catch (Exception e) {
                log.error("Kiwoom cancel API call failed - orderId: {}", orderId.value(), e);
                return OrderExecutionResult.rejected("Cancel API call failed: " + e.getMessage());
            }
        });
    }
    
    /**
     * 키움 취소 API 응답 처리
     */
    private OrderExecutionResult processCancelResponse(OrderId orderId, ResponseEntity<Map> response) {
        try {
            Map<String, Object> responseBody = response.getBody();
            
            if (responseBody == null || !response.getStatusCode().is2xxSuccessful()) {
                return OrderExecutionResult.rejected("Cancel request failed");
            }
            
            Integer code = (Integer) responseBody.get("Code");
            if (code != null && code == 200) {
                log.info("Order cancelled successfully - orderId: {}", orderId.value());
                return OrderExecutionResult.cancelled();
            } else {
                Map<String, Object> body = (Map<String, Object>) responseBody.get("Body");
                String errorMsg = body != null ? (String) body.get("msg1") : "Cancel failed";
                return OrderExecutionResult.rejected("Cancel rejected: " + errorMsg);
            }
            
        } catch (Exception e) {
            log.error("Failed to process cancel response - orderId: {}", orderId.value(), e);
            return OrderExecutionResult.rejected("Failed to process cancel response");
        }
    }
    
    
    /**
     * 주문 실행 결과 DTO
     */
    public static class OrderExecutionResult {
        private final ExecutionStatus status;
        private final String brokerOrderId;
        private final String message;
        private final Instant executedAt;
        
        private OrderExecutionResult(ExecutionStatus status, String brokerOrderId, String message) {
            this.status = status;
            this.brokerOrderId = brokerOrderId;
            this.message = message;
            this.executedAt = Instant.now();
        }
        
        public static OrderExecutionResult submitted(String brokerOrderId) {
            return new OrderExecutionResult(ExecutionStatus.SUBMITTED, brokerOrderId, "Order submitted to broker");
        }
        
        public static OrderExecutionResult rejected(String reason) {
            return new OrderExecutionResult(ExecutionStatus.REJECTED, null, reason);
        }
        
        public static OrderExecutionResult cancelled() {
            return new OrderExecutionResult(ExecutionStatus.CANCELLED, null, "Order cancelled");
        }
        
        // Getters
        public ExecutionStatus getStatus() { return status; }
        public String getBrokerOrderId() { return brokerOrderId; }
        public String getMessage() { return message; }
        public Instant getExecutedAt() { return executedAt; }
        
        public boolean isSuccessful() { 
            return status == ExecutionStatus.SUBMITTED || status == ExecutionStatus.CANCELLED; 
        }
        
        public enum ExecutionStatus {
            SUBMITTED, REJECTED, CANCELLED
        }
    }
}