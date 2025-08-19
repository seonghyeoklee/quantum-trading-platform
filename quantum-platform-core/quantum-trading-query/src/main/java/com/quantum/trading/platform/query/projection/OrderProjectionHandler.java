package com.quantum.trading.platform.query.projection;

import com.quantum.trading.platform.query.repository.OrderViewRepository;
import com.quantum.trading.platform.query.view.OrderView;
import com.quantum.trading.platform.shared.event.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

/**
 * 주문 이벤트를 구독하여 OrderView를 업데이트하는 Projection Handler
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class OrderProjectionHandler {
    
    private final OrderViewRepository orderViewRepository;
    
    /**
     * 주문 생성 이벤트 처리
     */
    @EventHandler
    public void on(OrderCreatedEvent event) {
        log.info("Processing OrderCreatedEvent: {}", event.getOrderId());
        
        OrderView orderView = OrderView.fromOrderCreated(
                event.getOrderId(),
                event.getUserId(),
                event.getSymbol(),
                event.getOrderType(),
                event.getSide(),
                event.getPrice(),
                event.getQuantity(),
                event.getTimestamp()
        );
        
        orderViewRepository.save(orderView);
        
        log.debug("OrderView created: {}", orderView.getOrderId());
    }
    
    /**
     * 주문 상태 변경 이벤트 처리
     */
    @EventHandler
    public void on(OrderStatusChangedEvent event) {
        log.info("Processing OrderStatusChangedEvent: {} -> {}", 
                event.getOrderId(), event.getNewStatus());
        
        orderViewRepository.findById(event.getOrderId().getValue())
                .ifPresentOrElse(
                        orderView -> {
                            orderView.updateStatus(
                                    event.getNewStatus(),
                                    event.getReason(),
                                    event.getTimestamp()
                            );
                            orderViewRepository.save(orderView);
                            log.debug("OrderView status updated: {} -> {}", 
                                    event.getOrderId(), event.getNewStatus());
                        },
                        () -> log.warn("OrderView not found for status update: {}", event.getOrderId())
                );
    }
    
    /**
     * 브로커 제출 이벤트 처리
     */
    @EventHandler
    public void on(OrderSubmittedToBrokerEvent event) {
        log.info("Processing OrderSubmittedToBrokerEvent: {} to {}", 
                event.getOrderId(), event.getBrokerType());
        
        orderViewRepository.findById(event.getOrderId().getValue())
                .ifPresentOrElse(
                        orderView -> {
                            orderView.updateBrokerInfo(
                                    event.getBrokerType(),
                                    null, // accountNumber is not in this event
                                    event.getSubmittedAt()
                            );
                            orderViewRepository.save(orderView);
                            log.debug("OrderView broker info updated: {}", event.getOrderId());
                        },
                        () -> log.warn("OrderView not found for broker submission: {}", event.getOrderId())
                );
    }
    
    /**
     * 주문 체결 이벤트 처리
     */
    @EventHandler
    public void on(OrderExecutedEvent event) {
        log.info("Processing OrderExecutedEvent: {} - {} shares @ {}", 
                event.getOrderId(), event.getExecutedQuantity(), event.getExecutedPrice());
        
        orderViewRepository.findById(event.getOrderId().getValue())
                .ifPresentOrElse(
                        orderView -> {
                            // Calculate total amount (price * quantity)
                            BigDecimal totalAmount = event.getExecutedPrice().getAmount()
                                    .multiply(BigDecimal.valueOf(event.getExecutedQuantity().getValue()));
                            
                            orderView.updateExecution(
                                    event.getExecutedQuantity().getValue(),
                                    event.getExecutedPrice().getAmount(),
                                    totalAmount,
                                    BigDecimal.ZERO, // fee calculation would be done separately
                                    event.getExecutedAt()
                            );
                            orderViewRepository.save(orderView);
                            log.debug("OrderView execution updated: {}", event.getOrderId());
                        },
                        () -> log.warn("OrderView not found for execution: {}", event.getOrderId())
                );
    }
    
    /**
     * 주문 취소 이벤트 처리
     */
    @EventHandler
    public void on(OrderCancelledEvent event) {
        log.info("Processing OrderCancelledEvent: {} - {}", 
                event.getOrderId(), event.getReason());
        
        orderViewRepository.findById(event.getOrderId().getValue())
                .ifPresentOrElse(
                        orderView -> {
                            orderView.updateStatus(
                                    event.getNewStatus(),
                                    event.getReason(),
                                    event.getTimestamp()
                            );
                            orderViewRepository.save(orderView);
                            log.debug("OrderView cancelled: {}", event.getOrderId());
                        },
                        () -> log.warn("OrderView not found for cancellation: {}", event.getOrderId())
                );
    }
    
    /**
     * 주문 거부 이벤트 처리
     */
    @EventHandler
    public void on(OrderRejectedEvent event) {
        log.info("Processing OrderRejectedEvent: {} - {}", 
                event.getOrderId(), event.getReason());
        
        orderViewRepository.findById(event.getOrderId().getValue())
                .ifPresentOrElse(
                        orderView -> {
                            orderView.updateStatus(
                                    event.getNewStatus(),
                                    event.getReason(),
                                    event.getTimestamp()
                            );
                            orderViewRepository.save(orderView);
                            log.debug("OrderView rejected: {}", event.getOrderId());
                        },
                        () -> log.warn("OrderView not found for rejection: {}", event.getOrderId())
                );
    }
}