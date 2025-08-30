package com.quantum.web.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.quantum.trading.platform.shared.command.CancelOrderCommand;
import com.quantum.trading.platform.shared.event.OrderExecutedEvent;
import com.quantum.trading.platform.shared.value.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.modelling.command.AggregateLifecycle;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.*;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.io.IOException;
import java.math.BigDecimal;
import java.net.URI;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 실시간 주문 상태 추적 서비스
 * 
 * 키움증권 WebSocket TR 데이터를 통해 주문의 실시간 상태를 추적하고
 * OrderExecutedEvent, OrderCancelledEvent 등을 자동으로 발행하는 서비스
 * 
 * 주요 기능:
 * - 키움 WebSocket 연결 관리
 * - TR 데이터 실시간 수신 및 파싱
 * - 주문 체결/취소 이벤트 자동 발행
 * - 연결 상태 모니터링 및 자동 재연결
 * - 주문 ID와 브로커 주문 ID 매핑 관리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class RealtimeOrderTrackingService {
    
    private final CommandGateway commandGateway;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);
    
    @Value("${kiwoom.adapter.base-url:http://localhost:10201}")
    private String kiwoomAdapterBaseUrl;
    
    @Value("${realtime.tracking.enabled:true}")
    private boolean realtimeTrackingEnabled;
    
    @Value("${realtime.reconnect.interval:5000}")
    private long reconnectInterval;
    
    @Value("${realtime.heartbeat.interval:30000}")
    private long heartbeatInterval;
    
    // 활성 주문 추적 맵 (브로커 주문 ID -> 내부 주문 정보)
    private final Map<String, TrackedOrder> trackedOrders = new ConcurrentHashMap<>();
    
    // WebSocket 연결 상태
    private WebSocketSession currentSession;
    private boolean isConnected = false;
    private boolean shouldReconnect = true;
    
    /**
     * 서비스 초기화 - WebSocket 연결 시작
     */
    @PostConstruct
    public void initialize() {
        if (realtimeTrackingEnabled) {
            log.info("🚀 Starting Realtime Order Tracking Service");
            connectToKiwoomWebSocket();
            startHeartbeatMonitor();
        } else {
            log.info("⏸️ Realtime Order Tracking Service is disabled");
        }
    }
    
    /**
     * 서비스 종료 - 연결 해제
     */
    @PreDestroy
    public void shutdown() {
        log.info("🛑 Shutting down Realtime Order Tracking Service");
        shouldReconnect = false;
        
        if (currentSession != null && currentSession.isOpen()) {
            try {
                currentSession.close();
            } catch (IOException e) {
                log.warn("Error closing WebSocket session", e);
            }
        }
        
        scheduler.shutdown();
        trackedOrders.clear();
    }
    
    /**
     * 주문 추적 시작
     * 
     * @param orderId 내부 주문 ID
     * @param brokerOrderId 브로커 주문 ID
     * @param userId 사용자 ID
     * @param symbol 종목코드
     * @param side 매매방향
     * @param quantity 주문수량
     * @param price 주문가격
     */
    public void startTracking(OrderId orderId, String brokerOrderId, UserId userId, 
                             Symbol symbol, OrderSide side, Quantity quantity, Money price) {
        
        if (!realtimeTrackingEnabled) {
            log.debug("Realtime tracking is disabled, skipping tracking for orderId: {}", orderId.value());
            return;
        }
        
        TrackedOrder trackedOrder = TrackedOrder.builder()
                .orderId(orderId)
                .brokerOrderId(brokerOrderId)
                .userId(userId)
                .symbol(symbol)
                .side(side)
                .originalQuantity(quantity)
                .price(price)
                .status(OrderStatus.SUBMITTED)
                .startedAt(Instant.now())
                .build();
        
        trackedOrders.put(brokerOrderId, trackedOrder);
        
        log.info("📍 Started tracking order - orderId: {}, brokerOrderId: {}, symbol: {}", 
                orderId.value(), brokerOrderId, symbol.value());
        
        // WebSocket을 통해 해당 주문 구독 요청
        subscribeToOrderUpdates(brokerOrderId);
    }
    
    /**
     * 주문 추적 중지
     */
    public void stopTracking(String brokerOrderId) {
        TrackedOrder trackedOrder = trackedOrders.remove(brokerOrderId);
        
        if (trackedOrder != null) {
            log.info("🛑 Stopped tracking order - orderId: {}, brokerOrderId: {}", 
                    trackedOrder.getOrderId().value(), brokerOrderId);
            
            // WebSocket 구독 해제
            unsubscribeFromOrderUpdates(brokerOrderId);
        }
    }
    
    /**
     * 키움 WebSocket 연결
     */
    private void connectToKiwoomWebSocket() {
        try {
            String wsUrl = kiwoomAdapterBaseUrl.replace("http", "ws") + "/ws/realtime";
            URI serverUri = URI.create(wsUrl);
            
            // TODO: WebSocket 연결 구현 필요
            // WebSocketConnectionManager connectionManager = new WebSocketConnectionManager(
            //         new StandardWebSocketClient(), 
            //         new KiwoomWebSocketHandler(), 
            //         wsUrl);
            // 
            // connectionManager.start();
            
            log.info("🔌 Attempting to connect to Kiwoom WebSocket: {}", wsUrl);
            log.warn("⚠️ WebSocket connection not implemented yet");
            
        } catch (Exception e) {
            log.error("❌ Failed to connect to Kiwoom WebSocket", e);
            scheduleReconnect();
        }
    }
    
    /**
     * WebSocket 재연결 스케줄링
     */
    private void scheduleReconnect() {
        if (shouldReconnect) {
            scheduler.schedule(() -> {
                log.info("🔄 Attempting WebSocket reconnection...");
                connectToKiwoomWebSocket();
            }, reconnectInterval, TimeUnit.MILLISECONDS);
        }
    }
    
    /**
     * 하트비트 모니터링 시작
     */
    private void startHeartbeatMonitor() {
        scheduler.scheduleWithFixedDelay(() -> {
            if (isConnected && currentSession != null && currentSession.isOpen()) {
                try {
                    // 하트비트 메시지 전송
                    sendHeartbeat();
                } catch (Exception e) {
                    log.warn("❤️ Heartbeat failed, connection may be lost", e);
                    isConnected = false;
                    scheduleReconnect();
                }
            }
        }, heartbeatInterval, heartbeatInterval, TimeUnit.MILLISECONDS);
    }
    
    /**
     * 주문 업데이트 구독
     */
    private void subscribeToOrderUpdates(String brokerOrderId) {
        if (currentSession != null && currentSession.isOpen()) {
            try {
                Map<String, Object> subscribeMessage = Map.of(
                        "type", "subscribe",
                        "channel", "order_updates",
                        "brokerOrderId", brokerOrderId
                );
                
                String message = objectMapper.writeValueAsString(subscribeMessage);
                currentSession.sendMessage(new TextMessage(message));
                
                log.debug("📡 Subscribed to order updates for brokerOrderId: {}", brokerOrderId);
                
            } catch (Exception e) {
                log.error("❌ Failed to subscribe to order updates for brokerOrderId: {}", brokerOrderId, e);
            }
        }
    }
    
    /**
     * 주문 업데이트 구독 해제
     */
    private void unsubscribeFromOrderUpdates(String brokerOrderId) {
        if (currentSession != null && currentSession.isOpen()) {
            try {
                Map<String, Object> unsubscribeMessage = Map.of(
                        "type", "unsubscribe", 
                        "channel", "order_updates",
                        "brokerOrderId", brokerOrderId
                );
                
                String message = objectMapper.writeValueAsString(unsubscribeMessage);
                currentSession.sendMessage(new TextMessage(message));
                
                log.debug("📡 Unsubscribed from order updates for brokerOrderId: {}", brokerOrderId);
                
            } catch (Exception e) {
                log.error("❌ Failed to unsubscribe from order updates for brokerOrderId: {}", brokerOrderId, e);
            }
        }
    }
    
    /**
     * 하트비트 메시지 전송
     */
    private void sendHeartbeat() throws IOException {
        if (currentSession != null && currentSession.isOpen()) {
            Map<String, Object> heartbeatMessage = Map.of(
                    "type", "heartbeat",
                    "timestamp", Instant.now().toString()
            );
            
            String message = objectMapper.writeValueAsString(heartbeatMessage);
            currentSession.sendMessage(new TextMessage(message));
            
            log.trace("❤️ Heartbeat sent");
        }
    }
    
    /**
     * 키움 WebSocket 메시지 처리
     */
    private void handleKiwoomMessage(String message) {
        try {
            JsonNode jsonNode = objectMapper.readTree(message);
            String messageType = jsonNode.get("type").asText();
            
            switch (messageType) {
                case "order_update" -> handleOrderUpdate(jsonNode);
                case "order_execution" -> handleOrderExecution(jsonNode);
                case "order_cancellation" -> handleOrderCancellation(jsonNode);
                case "heartbeat_response" -> handleHeartbeatResponse(jsonNode);
                case "error" -> handleErrorMessage(jsonNode);
                default -> log.debug("Unknown message type: {}", messageType);
            }
            
        } catch (Exception e) {
            log.error("❌ Failed to process WebSocket message: {}", message, e);
        }
    }
    
    /**
     * 주문 상태 업데이트 처리
     */
    private void handleOrderUpdate(JsonNode data) {
        try {
            String brokerOrderId = data.get("brokerOrderId").asText();
            String statusString = data.get("status").asText();
            OrderStatus newStatus = OrderStatus.valueOf(statusString);
            
            TrackedOrder trackedOrder = trackedOrders.get(brokerOrderId);
            if (trackedOrder == null) {
                log.warn("⚠️ Received update for unknown brokerOrderId: {}", brokerOrderId);
                return;
            }
            
            log.info("📊 Order status update - orderId: {}, brokerOrderId: {}, status: {} -> {}", 
                    trackedOrder.getOrderId().value(), brokerOrderId, trackedOrder.getStatus(), newStatus);
            
            // 상태 업데이트
            trackedOrder.setStatus(newStatus);
            trackedOrder.setLastUpdated(Instant.now());
            
            // TODO: OrderStatusChangedEvent 발행을 위한 Command 전송
            // 현재는 Aggregate에서만 이벤트를 발행할 수 있으므로 Command를 통해 처리
            
        } catch (Exception e) {
            log.error("❌ Failed to handle order update", e);
        }
    }
    
    /**
     * 주문 체결 처리
     */
    private void handleOrderExecution(JsonNode data) {
        try {
            String brokerOrderId = data.get("brokerOrderId").asText();
            BigDecimal executedPrice = new BigDecimal(data.get("executedPrice").asText());
            Integer executedQuantity = data.get("executedQuantity").asInt();
            Integer remainingQuantity = data.get("remainingQuantity").asInt();
            String executionId = data.get("executionId").asText();
            
            TrackedOrder trackedOrder = trackedOrders.get(brokerOrderId);
            if (trackedOrder == null) {
                log.warn("⚠️ Received execution for unknown brokerOrderId: {}", brokerOrderId);
                return;
            }
            
            log.info("✅ Order execution received - orderId: {}, brokerOrderId: {}, executedQuantity: {}, executedPrice: {}", 
                    trackedOrder.getOrderId().value(), brokerOrderId, executedQuantity, executedPrice);
            
            // 체결 정보 업데이트
            trackedOrder.addExecution(executedQuantity, executedPrice, executionId);
            
            // OrderExecutedEvent 발행을 위한 Aggregate 메서드 호출
            // 실제로는 TradingOrder Aggregate의 markAsExecuted 메서드를 호출해야 함
            notifyOrderExecution(trackedOrder, executedPrice, executedQuantity, remainingQuantity, executionId);
            
            // 완전 체결 시 추적 중지
            if (remainingQuantity == 0) {
                stopTracking(brokerOrderId);
            }
            
        } catch (Exception e) {
            log.error("❌ Failed to handle order execution", e);
        }
    }
    
    /**
     * 주문 취소 처리
     */
    private void handleOrderCancellation(JsonNode data) {
        try {
            String brokerOrderId = data.get("brokerOrderId").asText();
            String reason = data.get("reason").asText("User requested cancellation");
            
            TrackedOrder trackedOrder = trackedOrders.get(brokerOrderId);
            if (trackedOrder == null) {
                log.warn("⚠️ Received cancellation for unknown brokerOrderId: {}", brokerOrderId);
                return;
            }
            
            log.info("❌ Order cancellation received - orderId: {}, brokerOrderId: {}, reason: {}", 
                    trackedOrder.getOrderId().value(), brokerOrderId, reason);
            
            // 상태 업데이트
            trackedOrder.setStatus(OrderStatus.CANCELLED);
            trackedOrder.setLastUpdated(Instant.now());
            
            // 추적 중지
            stopTracking(brokerOrderId);
            
        } catch (Exception e) {
            log.error("❌ Failed to handle order cancellation", e);
        }
    }
    
    /**
     * 하트비트 응답 처리
     */
    private void handleHeartbeatResponse(JsonNode data) {
        log.trace("❤️ Heartbeat response received");
    }
    
    /**
     * 오류 메시지 처리
     */
    private void handleErrorMessage(JsonNode data) {
        String errorCode = data.get("code").asText();
        String errorMessage = data.get("message").asText();
        
        log.error("🚨 WebSocket error received - code: {}, message: {}", errorCode, errorMessage);
        
        // 특정 오류에 대한 처리
        switch (errorCode) {
            case "AUTHENTICATION_FAILED" -> {
                log.error("🔐 WebSocket authentication failed, stopping reconnection attempts");
                shouldReconnect = false;
            }
            case "SUBSCRIPTION_FAILED" -> {
                log.warn("📡 Subscription failed, will retry");
                // TODO: 구독 재시도 로직
            }
            default -> log.warn("Unknown error code: {}", errorCode);
        }
    }
    
    /**
     * 주문 체결 알림 (Aggregate에 체결 정보 전달)
     */
    private void notifyOrderExecution(TrackedOrder trackedOrder, BigDecimal executedPrice, 
                                    Integer executedQuantity, Integer remainingQuantity, String executionId) {
        
        // TODO: TradingOrder Aggregate의 markAsExecuted 메서드 호출
        // 현재 Axon Framework 구조상 직접적인 Aggregate 메서드 호출이 어려우므로
        // Command를 통해 처리하거나 다른 방식으로 구현 필요
        
        log.info("📤 Would notify order execution to aggregate - orderId: {}, executedQuantity: {}, executedPrice: {}", 
                trackedOrder.getOrderId().value(), executedQuantity, executedPrice);
    }
    
    // TODO: WebSocket Handler 구현 필요  
    /*
    private class KiwoomWebSocketHandler implements WebSocketHandler {
        // WebSocket Handler 구현...
    }
    */
    
    /**
     * 추적 중인 주문 정보
     */
    @lombok.Data
    @lombok.Builder
    public static class TrackedOrder {
        private OrderId orderId;
        private String brokerOrderId;
        private UserId userId;
        private Symbol symbol;
        private OrderSide side;
        private Quantity originalQuantity;
        private Money price;
        private OrderStatus status;
        private Instant startedAt;
        private Instant lastUpdated;
        
        // 체결 정보
        @lombok.Builder.Default
        private final java.util.List<Execution> executions = new java.util.ArrayList<>();
        
        public void addExecution(Integer quantity, BigDecimal price, String executionId) {
            executions.add(Execution.builder()
                    .quantity(quantity)
                    .price(price)
                    .executionId(executionId)
                    .timestamp(Instant.now())
                    .build());
        }
        
        public Integer getTotalExecutedQuantity() {
            return executions.stream()
                    .mapToInt(Execution::getQuantity)
                    .sum();
        }
        
        public BigDecimal getAverageExecutedPrice() {
            if (executions.isEmpty()) return BigDecimal.ZERO;
            
            BigDecimal totalAmount = executions.stream()
                    .map(e -> e.getPrice().multiply(BigDecimal.valueOf(e.getQuantity())))
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            
            Integer totalQuantity = getTotalExecutedQuantity();
            
            return totalQuantity > 0 
                    ? totalAmount.divide(BigDecimal.valueOf(totalQuantity), 2, BigDecimal.ROUND_HALF_UP)
                    : BigDecimal.ZERO;
        }
    }
    
    /**
     * 체결 정보
     */
    @lombok.Data
    @lombok.Builder
    public static class Execution {
        private Integer quantity;
        private BigDecimal price;
        private String executionId;
        private Instant timestamp;
    }
    
    /**
     * 현재 추적 중인 주문 수 반환
     */
    public int getActiveTrackingCount() {
        return trackedOrders.size();
    }
    
    /**
     * 연결 상태 확인
     */
    public boolean isConnected() {
        return isConnected;
    }
    
    /**
     * 특정 주문의 추적 정보 조회
     */
    public TrackedOrder getTrackedOrder(String brokerOrderId) {
        return trackedOrders.get(brokerOrderId);
    }
}