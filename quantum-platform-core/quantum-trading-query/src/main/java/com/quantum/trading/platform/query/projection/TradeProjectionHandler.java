package com.quantum.trading.platform.query.projection;

import com.quantum.trading.platform.query.repository.TradeViewRepository;
import com.quantum.trading.platform.query.repository.OrderViewRepository;
import com.quantum.trading.platform.query.view.TradeView;
import com.quantum.trading.platform.query.view.OrderView;
import com.quantum.trading.platform.shared.event.OrderExecutedEvent;
import com.quantum.trading.platform.shared.event.TradeExecutedEvent;
import com.quantum.trading.platform.shared.value.OrderSide;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.UUID;

/**
 * 거래 이력 Projection Handler
 * 
 * OrderExecutedEvent를 수신하여 TradeView를 생성하고
 * TradeExecutedEvent를 발행하여 외부 알림 시스템에 전달
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class TradeProjectionHandler {
    
    private final TradeViewRepository tradeViewRepository;
    private final OrderViewRepository orderViewRepository;
    private final ApplicationEventPublisher eventPublisher;
    
    // 한국 주식 거래 수수료 및 세금
    private static final BigDecimal TRANSACTION_FEE_RATE = new BigDecimal("0.00015"); // 0.015%
    private static final BigDecimal SECURITIES_TAX_RATE = new BigDecimal("0.003"); // 0.3% (매도시만)
    
    /**
     * 주문 체결 이벤트 처리 - 거래 이력 생성
     */
    @EventHandler
    @Transactional
    public void on(OrderExecutedEvent event) {
        log.info("🏪 Processing OrderExecutedEvent for trade history - orderId: {}, quantity: {}, price: {}", 
                event.getOrderId().value(), 
                event.getExecutedQuantity().value(),
                event.getExecutedPrice().amount());
        
        try {
            // 1. OrderView에서 주문 정보 조회 (Symbol, Side, UserId 등 획득)
            OrderView orderView = orderViewRepository.findById(event.getOrderId().value())
                    .orElse(null);
                    
            if (orderView == null) {
                log.warn("⚠️ OrderView not found for OrderExecutedEvent - orderId: {}", event.getOrderId().value());
                return;
            }
            
            // 2. 거래 ID 생성
            String tradeId = generateTradeId(event);
            
            // 3. 거래 수수료 및 세금 계산
            BigDecimal executedAmount = event.getExecutedPrice().amount()
                    .multiply(BigDecimal.valueOf(event.getExecutedQuantity().value()));
            
            BigDecimal transactionFee = executedAmount.multiply(TRANSACTION_FEE_RATE)
                    .setScale(2, RoundingMode.HALF_UP);
            
            BigDecimal securitiesTax = BigDecimal.ZERO;
            BigDecimal netAmount = executedAmount;
            
            // 매도시에만 증권거래세 적용
            if (orderView.getSide() == OrderSide.SELL) {
                securitiesTax = executedAmount.multiply(SECURITIES_TAX_RATE)
                        .setScale(2, RoundingMode.HALF_UP);
                netAmount = executedAmount.subtract(transactionFee).subtract(securitiesTax);
            } else {
                // 매수시에는 수수료만 추가
                netAmount = executedAmount.add(transactionFee);
            }
            
            // 4. P&L 계산 (매도시)
            BigDecimal averageCost = null;
            BigDecimal realizedPnL = null;
            BigDecimal realizedPnLRate = null;
            
            if (orderView.getSide() == OrderSide.SELL) {
                // TODO: 실제 구현에서는 PositionView에서 평균 매입가 조회
                // 임시로 예시 데이터 사용
                averageCost = new BigDecimal("70000"); // 임시값
                realizedPnL = event.getExecutedPrice().amount().subtract(averageCost)
                        .multiply(BigDecimal.valueOf(event.getExecutedQuantity().value()))
                        .subtract(transactionFee).subtract(securitiesTax);
                
                if (averageCost.compareTo(BigDecimal.ZERO) > 0) {
                    realizedPnLRate = event.getExecutedPrice().amount().subtract(averageCost)
                            .divide(averageCost, 6, RoundingMode.HALF_UP)
                            .multiply(BigDecimal.valueOf(100));
                }
            }
            
            // 5. TradeView 엔티티 생성
            TradeView tradeView = TradeView.builder()
                    .tradeId(tradeId)
                    .orderId(event.getOrderId().value())
                    .userId(orderView.getUserId())
                    .portfolioId(orderView.getPortfolioId())
                    .symbol(orderView.getSymbol())
                    .symbolName(getSymbolName(orderView.getSymbol()))
                    .side(orderView.getSide())
                    .executedQuantity(event.getExecutedQuantity().value())
                    .executedPrice(event.getExecutedPrice().amount())
                    .executedAmount(executedAmount)
                    .transactionFee(transactionFee)
                    .securitiesTax(securitiesTax)
                    .netAmount(netAmount)
                    .brokerOrderId(event.getBrokerOrderId())
                    .brokerTradeId(generateBrokerTradeId(event))
                    .executedAt(convertToLocalDateTime(event.getExecutedAt()))
                    .settlementDate(calculateSettlementDate(event.getExecutedAt()))
                    .averageCost(averageCost)
                    .realizedPnL(realizedPnL)
                    .realizedPnLRate(realizedPnLRate)
                    .notes("Executed via Quantum Trading Platform")
                    .build();
            
            // 6. 거래 이력 저장
            TradeView savedTrade = tradeViewRepository.save(tradeView);
            log.info("✅ Trade history saved - tradeId: {}, orderId: {}, side: {}, amount: {}", 
                    savedTrade.getTradeId(), savedTrade.getOrderId(), 
                    savedTrade.getSide(), savedTrade.getExecutedAmount());
            
            // 7. TradeExecutedEvent 발행 (알림용)
            publishTradeExecutedEvent(savedTrade, orderView, event);
            
        } catch (Exception e) {
            log.error("🚨 Failed to process OrderExecutedEvent for trade history - orderId: {}", 
                    event.getOrderId().value(), e);
        }
    }
    
    /**
     * 거래 ID 생성
     */
    private String generateTradeId(OrderExecutedEvent event) {
        return String.format("TRADE-%s-%s", 
                event.getOrderId().value().replace("ORDER-", ""), 
                System.currentTimeMillis());
    }
    
    /**
     * 브로커 거래 ID 생성 (실제로는 브로커에서 제공)
     */
    private String generateBrokerTradeId(OrderExecutedEvent event) {
        if (event.getBrokerOrderId() != null) {
            return "TRD-" + event.getBrokerOrderId() + "-" + UUID.randomUUID().toString().substring(0, 8);
        }
        return "TRD-" + UUID.randomUUID().toString().substring(0, 12);
    }
    
    /**
     * 종목명 조회 (실제로는 Symbol Master Table에서)
     */
    private String getSymbolName(String symbol) {
        // TODO: Symbol Master Table에서 종목명 조회
        return switch (symbol) {
            case "005930" -> "삼성전자";
            case "000660" -> "SK하이닉스";
            case "035420" -> "NAVER";
            case "051910" -> "LG화학";
            case "006400" -> "삼성SDI";
            default -> symbol; // 임시로 종목코드 반환
        };
    }
    
    /**
     * Instant를 LocalDateTime으로 변환
     */
    private LocalDateTime convertToLocalDateTime(Instant instant) {
        return instant != null ? 
                LocalDateTime.ofInstant(instant, ZoneId.systemDefault()) : 
                LocalDateTime.now();
    }
    
    /**
     * 결제일 계산 (T+2)
     */
    private LocalDateTime calculateSettlementDate(Instant executedAt) {
        LocalDateTime executed = convertToLocalDateTime(executedAt);
        return executed.plusDays(2); // 한국 주식 T+2 결제
    }
    
    /**
     * TradeExecutedEvent 발행 (알림용)
     */
    private void publishTradeExecutedEvent(TradeView tradeView, OrderView orderView, OrderExecutedEvent originalEvent) {
        try {
            // 임시로 간단한 알림 이벤트 생성 (TradeExecutedEvent 구조를 간소화)
            // 실제로는 TradeExecutedEvent를 더 간단하게 만들거나 별도의 알림 이벤트를 만들 수 있음
            
            log.info("📢 Trade execution notification - tradeId: {}, orderId: {}, symbol: {}, side: {}, quantity: {}, price: {}, amount: {}", 
                    tradeView.getTradeId(),
                    tradeView.getOrderId(),
                    tradeView.getSymbol(),
                    tradeView.getSide(),
                    tradeView.getExecutedQuantity(),
                    tradeView.getExecutedPrice(),
                    tradeView.getExecutedAmount());
            
            // 파이썬 어댑터나 슬랙 알림 모듈에서 구독할 수 있는 간단한 이벤트 발행
            // Spring ApplicationEvent를 통해 느슨한 결합으로 알림 처리
            TradeNotificationEvent notificationEvent = new TradeNotificationEvent(
                    tradeView.getTradeId(),
                    tradeView.getOrderId(),
                    tradeView.getUserId(),
                    tradeView.getPortfolioId(),
                    tradeView.getSymbol(),
                    tradeView.getSymbolName(),
                    tradeView.getSide(),
                    tradeView.getExecutedQuantity(),
                    tradeView.getExecutedPrice(),
                    tradeView.getExecutedAmount(),
                    tradeView.getTransactionFee(),
                    tradeView.getSecuritiesTax(),
                    tradeView.getNetAmount(),
                    tradeView.getRealizedPnL(),
                    tradeView.getExecutedAt(),
                    originalEvent.getExecutedAt()
            );
            
            eventPublisher.publishEvent(notificationEvent);
            
            log.info("📢 TradeNotificationEvent published for external systems - tradeId: {}", tradeView.getTradeId());
            
        } catch (Exception e) {
            log.error("🚨 Failed to publish TradeNotificationEvent - tradeId: {}", tradeView.getTradeId(), e);
        }
    }
    
    /**
     * 간소화된 거래 알림 이벤트 (내부 클래스)
     */
    public record TradeNotificationEvent(
            String tradeId,
            String orderId,
            String userId,
            String portfolioId,
            String symbol,
            String symbolName,
            OrderSide side,
            Integer executedQuantity,
            BigDecimal executedPrice,
            BigDecimal executedAmount,
            BigDecimal transactionFee,
            BigDecimal securitiesTax,
            BigDecimal netAmount,
            BigDecimal realizedPnL,
            LocalDateTime executedAt,
            Instant originalExecutedAt
    ) {}
}