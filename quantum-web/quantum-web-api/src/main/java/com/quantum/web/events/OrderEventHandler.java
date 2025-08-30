package com.quantum.web.events;

import com.quantum.trading.platform.shared.command.SubmitOrderToBrokerCommand;
import com.quantum.trading.platform.shared.event.*;
import com.quantum.trading.platform.shared.value.Money;
import com.quantum.trading.platform.shared.value.OrderId;
import com.quantum.trading.platform.shared.value.OrderStatus;
import com.quantum.trading.platform.shared.value.Quantity;
import com.quantum.trading.platform.shared.value.Symbol;
import com.quantum.trading.platform.query.service.OrderQueryService;
import com.quantum.trading.platform.query.view.OrderView;
import com.quantum.web.service.OrderExecutionService;
import com.quantum.web.service.RealtimeOrderTrackingService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.modelling.command.AggregateLifecycle;
import org.springframework.stereotype.Component;

import java.time.Instant;

/**
 * 주문 관련 Event Handler
 * 
 * CQRS Event Sourcing 패턴에서 Domain Event를 처리하여 
 * 외부 시스템(키움증권 API)과 연동하는 핵심 컴포넌트
 * 
 * 처리 흐름:
 * 1. OrderCreatedEvent → 키움 API 주문 제출
 * 2. OrderSubmittedToBrokerEvent → 실시간 상태 추적 시작  
 * 3. OrderExecutedEvent → Portfolio 업데이트 및 알림
 * 4. OrderCancelledEvent → 키움 API 취소 요청
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class OrderEventHandler {
    
    private final OrderExecutionService orderExecutionService;
    private final RealtimeOrderTrackingService realtimeOrderTrackingService;
    private final CommandGateway commandGateway;
    private final OrderQueryService orderQueryService;
    
    /**
     * 주문 생성 이벤트 처리 - 키움 API로 자동 제출
     * 
     * OrderCreatedEvent 발생 시 자동으로 키움증권 API를 호출하여 주문을 제출합니다.
     * 이는 Event-Driven Architecture의 핵심으로, 도메인 이벤트가 외부 시스템과의 
     * 연동을 자동화합니다.
     * 
     * @param event OrderCreatedEvent 도메인 이벤트
     */
    @EventHandler
    public void on(OrderCreatedEvent event) {
        log.info("🔔 OrderCreatedEvent received - orderId: {}, symbol: {}, side: {}, quantity: {}", 
                event.orderId().value(), 
                event.symbol().value(),
                event.side().name(),
                event.quantity().value());
        
        try {
            // 1. 키움 API를 통한 주문 실행 (비동기)
            orderExecutionService.executeOrder(event)
                    .thenAccept(result -> {
                        if (result.isSuccessful()) {
                            // 성공 시 브로커 제출 이벤트 발행
                            handleSuccessfulSubmission(event, result);
                        } else {
                            // 실패 시 거부 이벤트 발행
                            handleFailedSubmission(event, result);
                        }
                    })
                    .exceptionally(throwable -> {
                        log.error("🚨 Order execution failed unexpectedly - orderId: {}", 
                                event.orderId().value(), throwable);
                        handleExecutionException(event, throwable);
                        return null;
                    });
            
        } catch (Exception e) {
            log.error("🚨 Failed to initiate order execution - orderId: {}", 
                    event.orderId().value(), e);
            handleExecutionException(event, e);
        }
    }
    
    /**
     * 주문 제출 성공 처리
     */
    private void handleSuccessfulSubmission(OrderCreatedEvent event, OrderExecutionService.OrderExecutionResult result) {
        log.info("✅ Order submitted to broker successfully - orderId: {}, brokerOrderId: {}", 
                event.orderId().value(), result.getBrokerOrderId());
        
        try {
            // SubmitOrderToBrokerCommand 발행으로 Aggregate 상태 업데이트
            SubmitOrderToBrokerCommand command = SubmitOrderToBrokerCommand.builder()
                    .orderId(event.orderId())
                    .userId(event.userId())
                    .brokerType("KIWOOM")
                    .brokerOrderId(result.getBrokerOrderId())
                    .submittedAt(result.getExecutedAt())
                    .build();
            
            commandGateway.send(command)
                    .thenRun(() -> {
                        log.info("📤 SubmitOrderToBrokerCommand sent successfully - orderId: {}", 
                                event.orderId().value());
                    })
                    .exceptionally(throwable -> {
                        log.error("🚨 Failed to send SubmitOrderToBrokerCommand - orderId: {}", 
                                event.orderId().value(), throwable);
                        return null;
                    });
            
        } catch (Exception e) {
            log.error("🚨 Failed to handle successful submission - orderId: {}", 
                    event.orderId().value(), e);
        }
    }
    
    /**
     * 주문 제출 실패 처리
     */
    private void handleFailedSubmission(OrderCreatedEvent event, OrderExecutionService.OrderExecutionResult result) {
        log.warn("⚠️ Order submission rejected by broker - orderId: {}, reason: {}", 
                event.orderId().value(), result.getMessage());
        
        try {
            // OrderRejectedEvent를 통한 상태 업데이트는 Aggregate에서 처리
            // 여기서는 로깅 및 외부 알림만 처리
            
            // TODO: 사용자에게 주문 거부 알림 전송
            // notificationService.notifyOrderRejected(event.userId(), event.orderId(), result.getMessage());
            
            log.info("📧 Order rejection notification would be sent to user: {}", event.userId().value());
            
        } catch (Exception e) {
            log.error("🚨 Failed to handle failed submission - orderId: {}", 
                    event.orderId().value(), e);
        }
    }
    
    /**
     * 주문 실행 예외 처리
     */
    private void handleExecutionException(OrderCreatedEvent event, Throwable throwable) {
        log.error("🚨 Order execution exception - orderId: {}", event.orderId().value(), throwable);
        
        try {
            // 시스템 오류로 인한 주문 실패 처리
            // TODO: 시스템 관리자에게 알림, 재시도 로직 등
            
            log.warn("🔄 Order execution failed due to system error - manual intervention may be required");
            
        } catch (Exception e) {
            log.error("🚨 Failed to handle execution exception - orderId: {}", 
                    event.orderId().value(), e);
        }
    }
    
    /**
     * 브로커 주문 제출 이벤트 처리 - 실시간 상태 추적 시작
     * 
     * @param event OrderSubmittedToBrokerEvent
     */
    @EventHandler  
    public void on(OrderSubmittedToBrokerEvent event) {
        log.info("🔔 OrderSubmittedToBrokerEvent received - orderId: {}, brokerType: {}, brokerOrderId: {}", 
                event.orderId().value(), 
                event.brokerType(),
                event.brokerOrderId());
        
        try {
            // 실시간 주문 상태 추적 시작
            startRealtimeOrderTracking(event);
            
            // 사용자에게 주문 접수 알림
            notifyOrderSubmitted(event);
            
        } catch (Exception e) {
            log.error("🚨 Failed to process OrderSubmittedToBrokerEvent - orderId: {}", 
                    event.orderId().value(), e);
        }
    }
    
    /**
     * 주문 체결 이벤트 처리 - Portfolio 업데이트
     * 
     * @param event OrderExecutedEvent
     */
    @EventHandler
    public void on(OrderExecutedEvent event) {
        log.info("🔔 OrderExecutedEvent received - orderId: {}, executedQuantity: {}, executedPrice: {}", 
                event.getOrderId().value(),
                event.getExecutedQuantity().value(),
                event.getExecutedPrice().amount());
        
        try {
            // Portfolio 업데이트를 위한 Command 발행
            updatePortfolioAfterExecution(event);
            
            // 사용자에게 체결 알림
            notifyOrderExecuted(event);
            
            // 체결 내역을 거래 이력에 기록
            recordTradeHistory(event);
            
        } catch (Exception e) {
            log.error("🚨 Failed to process OrderExecutedEvent - orderId: {}", 
                    event.getOrderId().value(), e);
        }
    }
    
    /**
     * 주문 취소 이벤트 처리 - 키움 API 취소 요청
     * 
     * @param event OrderStatusChangedEvent (CANCELLED 상태)
     */
    @EventHandler
    public void on(OrderStatusChangedEvent event) {
        log.info("🔔 OrderStatusChangedEvent received - orderId: {}, from: {}, to: {}", 
                event.orderId().value(),
                event.previousStatus().name(),
                event.newStatus().name());
        
        try {
            // 상태별 처리
            switch (event.newStatus()) {
                case CANCELLED -> handleOrderCancellation(event);
                case REJECTED -> handleOrderRejection(event);
                case FILLED -> handleOrderCompletion(event);
                case PARTIALLY_FILLED -> handlePartialExecution(event);
                default -> log.debug("Order status changed to: {}", event.newStatus());
            }
            
        } catch (Exception e) {
            log.error("🚨 Failed to process OrderStatusChangedEvent - orderId: {}", 
                    event.orderId().value(), e);
        }
    }
    
    /**
     * 실시간 주문 상태 추적 시작
     */
    private void startRealtimeOrderTracking(OrderSubmittedToBrokerEvent event) {
        log.info("🔍 Starting realtime order tracking - orderId: {}, brokerOrderId: {}", 
                event.orderId().value(), event.brokerOrderId());
        
        try {
            // OrderView에서 주문 정보 조회하여 실시간 추적에 필요한 데이터 획득
            OrderView orderView = orderQueryService.findOrderById(event.orderId());
            
            if (orderView == null) {
                log.warn("⚠️ OrderView not found for orderId: {}", event.orderId().value());
                return;
            }
            
            realtimeOrderTrackingService.startTracking(
                    event.orderId(),
                    event.brokerOrderId(),
                    event.userId(),
                    Symbol.of(orderView.getSymbol()),
                    orderView.getSide(),
                    Quantity.of(orderView.getQuantity()),
                    Money.of(orderView.getPrice())
            );
            
            log.info("✅ Real-time tracking started for order: {} (symbol: {}, side: {}, quantity: {})", 
                    event.orderId().value(), 
                    orderView.getSymbol(),
                    orderView.getSide().name(),
                    orderView.getQuantity());
            
        } catch (Exception e) {
            log.error("🚨 Failed to start realtime tracking - orderId: {}", 
                    event.orderId().value(), e);
        }
    }
    
    /**
     * Portfolio 업데이트
     */
    private void updatePortfolioAfterExecution(OrderExecutedEvent event) {
        log.info("💼 Updating portfolio after order execution - orderId: {}", 
                event.getOrderId().value());
        
        // TODO: UpdatePositionCommand 발행
        // - 매수: 보유 수량 증가, 현금 감소
        // - 매도: 보유 수량 감소, 현금 증가
        // - 평균 매입가 재계산
        // - 손익 계산
    }
    
    /**
     * 주문 접수 알림
     */
    private void notifyOrderSubmitted(OrderSubmittedToBrokerEvent event) {
        log.info("📧 Notifying order submission - orderId: {}", event.orderId().value());
        
        // TODO: 실시간 알림 서비스 구현
        // - WebSocket을 통한 실시간 알림
        // - 이메일/SMS 알림 (옵션)
        // - 모바일 푸시 알림 (옵션)
    }
    
    /**
     * 주문 체결 알림
     */
    private void notifyOrderExecuted(OrderExecutedEvent event) {
        log.info("📧 Notifying order execution - orderId: {}", event.getOrderId().value());
        
        // TODO: 체결 알림 구현
    }
    
    /**
     * 거래 이력 기록
     * 
     * OrderExecutedEvent는 TradeProjectionHandler에서 자동으로 처리되어
     * TradeView가 생성되고 TradeExecutedEvent가 발행됩니다.
     * 
     * 여기서는 추가적인 비즈니스 로직이나 외부 시스템 연동이 필요한 경우에만 사용합니다.
     */
    private void recordTradeHistory(OrderExecutedEvent event) {
        log.info("📝 Trade history recording handled by TradeProjectionHandler - orderId: {} will generate TradeExecutedEvent", 
                event.getOrderId().value());
        
        // TradeProjectionHandler가 다음을 자동 처리:
        // ✅ TradeView 생성 및 저장
        // ✅ 거래 수수료 및 세금 계산 (한국 주식 기준)
        // ✅ 손익 계산 (매도시)
        // ✅ TradeExecutedEvent 발행 (외부 알림 시스템용)
        
        // 필요시 추가 비즈니스 로직 구현 위치
        // - 특수한 세금 계산 로직
        // - 외부 회계 시스템 연동
        // - 특별한 통계 처리
        
        log.debug("🔄 TradeExecutedEvent will be published automatically for external notification systems");
    }
    
    /**
     * 주문 취소 처리
     */
    private void handleOrderCancellation(OrderStatusChangedEvent event) {
        log.info("❌ Processing order cancellation - orderId: {}", event.orderId().value());
        
        // TODO: 취소 후속 처리
        // - 취소 수수료 계산 (있을 경우)
        // - 사용자 알림
        // - 취소 이력 저장
    }
    
    /**
     * 주문 거부 처리  
     */
    private void handleOrderRejection(OrderStatusChangedEvent event) {
        log.warn("⚠️ Processing order rejection - orderId: {}, reason: {}", 
                event.orderId().value(), event.reason());
        
        // TODO: 거부 후속 처리
        // - 거부 사유 분석
        // - 사용자에게 상세 안내
        // - 재주문 제안 (조건 수정)
    }
    
    /**
     * 주문 완전 체결 처리
     */
    private void handleOrderCompletion(OrderStatusChangedEvent event) {
        log.info("✅ Order completed - orderId: {}", event.orderId().value());
        
        // TODO: 완전 체결 후속 처리
        // - 최종 손익 계산
        // - 세금 계산
        // - 성과 분석 업데이트
    }
    
    /**
     * 부분 체결 처리
     */
    private void handlePartialExecution(OrderStatusChangedEvent event) {
        log.info("🔄 Order partially executed - orderId: {}", event.orderId().value());
        
        // TODO: 부분 체결 처리
        // - 잔량 주문 관리
        // - 중간 손익 계산
        // - 사용자에게 부분 체결 알림
    }
}