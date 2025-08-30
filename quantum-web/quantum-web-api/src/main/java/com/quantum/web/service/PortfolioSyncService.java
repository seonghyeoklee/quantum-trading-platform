package com.quantum.web.service;

import com.quantum.trading.platform.query.service.PortfolioQueryService;
import com.quantum.trading.platform.query.view.PortfolioView;
import com.quantum.trading.platform.shared.command.UpdatePositionCommand;
import com.quantum.trading.platform.shared.event.OrderExecutedEvent;
import com.quantum.trading.platform.shared.event.OrderStatusChangedEvent;
import com.quantum.trading.platform.shared.value.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.concurrent.CompletableFuture;

/**
 * 포트폴리오 실시간 동기화 서비스
 * 
 * 주문 체결 이벤트를 수신하여 포트폴리오의 포지션과 현금을 실시간으로 업데이트:
 * - 매수 체결: 현금 차감, 포지션 증가, 평균 매입가 업데이트
 * - 매도 체결: 현금 증가, 포지션 감소, 실현손익 계산
 * - 수수료 및 세금 자동 계산
 * - 포트폴리오 총 가치 실시간 업데이트
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class PortfolioSyncService {
    
    private final CommandGateway commandGateway;
    private final PortfolioQueryService portfolioQueryService;
    
    // 한국 주식 거래 수수료 및 세금 (설정으로 분리 가능)
    private static final BigDecimal TRANSACTION_FEE_RATE = new BigDecimal("0.00015"); // 0.015%
    private static final BigDecimal SECURITIES_TAX_RATE = new BigDecimal("0.003"); // 0.3% (매도시만)
    
    /**
     * 주문 체결 이벤트 처리 - 포트폴리오 포지션 실시간 업데이트
     * 
     * @param event OrderExecutedEvent 주문 체결 이벤트
     */
    @EventHandler
    public void on(OrderExecutedEvent event) {
        log.info("🔔 OrderExecutedEvent received for portfolio sync - orderId: {}, quantity: {}, price: {}", 
                event.getOrderId().value(), 
                event.getExecutedQuantity().value(),
                event.getExecutedPrice().amount());
        
        try {
            // 1. 체결 정보 추출
            OrderId orderId = event.getOrderId();
            Quantity executedQuantity = event.getExecutedQuantity();
            Money executedPrice = event.getExecutedPrice();
            String brokerOrderId = event.getBrokerOrderId();
            
            // 2. 주문 정보 조회 (OrderView에서 사용자, 포트폴리오, 종목, 매매방향 등 획득)
            // TODO: OrderQueryService에서 주문 정보 조회
            // 현재는 임시로 기본값 사용하여 구조를 구현
            
            // 임시 데이터 (실제로는 OrderView에서 조회)
            UserId userId = UserId.of("USER-CURRENT"); // TODO: 실제 조회
            PortfolioId portfolioId = PortfolioId.of("PORTFOLIO-DEFAULT"); // TODO: 실제 조회  
            Symbol symbol = Symbol.of("005930"); // TODO: 실제 조회 (삼성전자 예시)
            OrderSide side = OrderSide.BUY; // TODO: 실제 조회
            
            // 3. 매매방향에 따른 포지션 업데이트
            if (side == OrderSide.BUY) {
                processBuyExecution(userId, portfolioId, symbol, executedQuantity, executedPrice, brokerOrderId);
            } else {
                processSellExecution(userId, portfolioId, symbol, executedQuantity, executedPrice, brokerOrderId);
            }
            
        } catch (Exception e) {
            log.error("🚨 Failed to process OrderExecutedEvent for portfolio sync - orderId: {}", 
                    event.getOrderId().value(), e);
        }
    }
    
    /**
     * 매수 체결 처리 - 포지션 증가, 현금 차감, 평균 매입가 업데이트
     */
    private void processBuyExecution(UserId userId, PortfolioId portfolioId, Symbol symbol, 
                                   Quantity executedQuantity, Money executedPrice, String brokerOrderId) {
        
        log.info("💰 Processing BUY execution - portfolio: {}, symbol: {}, quantity: {}, price: {}", 
                portfolioId.id(), symbol.value(), executedQuantity.value(), executedPrice.amount());
        
        try {
            // 1. 현재 포트폴리오 상태 조회
            PortfolioView portfolio = portfolioQueryService.findByPortfolioId(portfolioId);
            if (portfolio == null) {
                log.error("❌ Portfolio not found: {}", portfolioId.id());
                return;
            }
            
            // 2. 거래 비용 계산
            Money totalTradeAmount = executedPrice.multiply(executedQuantity.value());
            Money transactionFee = totalTradeAmount.multiply(TRANSACTION_FEE_RATE);
            Money totalCost = totalTradeAmount.add(transactionFee);
            
            log.info("💵 Trade cost calculation - amount: {}, fee: {}, total: {}", 
                    totalTradeAmount.amount(), transactionFee.amount(), totalCost.amount());
            
            // 3. 현재 포지션 조회 (해당 종목의 기존 보유량)
            // TODO: PositionQueryService 구현 후 실제 포지션 조회
            Quantity currentQuantity = Quantity.of(0); // 임시값
            Money currentAveragePrice = Money.of(BigDecimal.ZERO); // 임시값
            
            // 4. 새로운 평균 매입가 계산
            BigDecimal newQuantityTotal = BigDecimal.valueOf(currentQuantity.value() + executedQuantity.value());
            BigDecimal currentTotalValue = currentAveragePrice.amount()
                    .multiply(BigDecimal.valueOf(currentQuantity.value()));
            BigDecimal executedTotalValue = executedPrice.amount()
                    .multiply(BigDecimal.valueOf(executedQuantity.value()));
            
            Money newAveragePrice = Money.of(
                    currentTotalValue.add(executedTotalValue)
                            .divide(newQuantityTotal, 2, RoundingMode.HALF_UP)
            );
            
            Quantity newTotalQuantity = Quantity.of(newQuantityTotal.intValue());
            
            // 5. UpdatePositionCommand 발행
            UpdatePositionCommand command = UpdatePositionCommand.builder()
                    .portfolioId(portfolioId)
                    .orderId(OrderId.of("ORDER-FROM-BROKER-" + brokerOrderId)) // 임시 OrderId 생성
                    .symbol(symbol)
                    .side(OrderSide.BUY)
                    .quantity(executedQuantity)
                    .price(executedPrice)
                    .totalAmount(totalCost) // 수수료 포함된 총 비용
                    .build();
            
            // 6. CommandGateway로 포지션 업데이트 명령 발행
            commandGateway.send(command)
                    .thenRun(() -> {
                        log.info("✅ BUY position update completed - symbol: {}, newQuantity: {}, newAvgPrice: {}", 
                                symbol.value(), newTotalQuantity.value(), newAveragePrice.amount());
                    })
                    .exceptionally(throwable -> {
                        log.error("🚨 Failed to update BUY position - portfolio: {}, symbol: {}", 
                                portfolioId.id(), symbol.value(), throwable);
                        return null;
                    });
            
        } catch (Exception e) {
            log.error("🚨 Failed to process BUY execution - portfolio: {}, symbol: {}", 
                    portfolioId.id(), symbol.value(), e);
        }
    }
    
    /**
     * 매도 체결 처리 - 포지션 감소, 현금 증가, 실현손익 계산
     */
    private void processSellExecution(UserId userId, PortfolioId portfolioId, Symbol symbol, 
                                    Quantity executedQuantity, Money executedPrice, String brokerOrderId) {
        
        log.info("💸 Processing SELL execution - portfolio: {}, symbol: {}, quantity: {}, price: {}", 
                portfolioId.id(), symbol.value(), executedQuantity.value(), executedPrice.amount());
        
        try {
            // 1. 현재 포트폴리오 상태 조회
            PortfolioView portfolio = portfolioQueryService.findByPortfolioId(portfolioId);
            if (portfolio == null) {
                log.error("❌ Portfolio not found: {}", portfolioId.id());
                return;
            }
            
            // 2. 거래 비용 계산 (매도시 증권거래세 포함)
            Money totalTradeAmount = executedPrice.multiply(executedQuantity.value());
            Money transactionFee = totalTradeAmount.multiply(TRANSACTION_FEE_RATE);
            Money securitiesTax = totalTradeAmount.multiply(SECURITIES_TAX_RATE);
            Money totalFeeAndTax = transactionFee.add(securitiesTax);
            Money netReceived = totalTradeAmount.subtract(totalFeeAndTax);
            
            log.info("💵 Sell calculation - amount: {}, fee: {}, tax: {}, net: {}", 
                    totalTradeAmount.amount(), transactionFee.amount(), 
                    securitiesTax.amount(), netReceived.amount());
            
            // 3. 현재 포지션 조회 (해당 종목의 기존 보유량과 평균 매입가)
            // TODO: PositionQueryService 구현 후 실제 포지션 조회
            Quantity currentQuantity = Quantity.of(100); // 임시값 (보유 수량)
            Money currentAveragePrice = Money.of(new BigDecimal("70000")); // 임시값 (평균 매입가)
            
            // 4. 매도 후 잔여 수량 계산
            Quantity remainingQuantity = Quantity.of(currentQuantity.value() - executedQuantity.value());
            
            // 5. 실현손익 계산
            Money costBasis = currentAveragePrice.multiply(executedQuantity.value());
            Money realizedPnL = totalTradeAmount.subtract(costBasis).subtract(totalFeeAndTax);
            
            log.info("📊 P&L calculation - costBasis: {}, realizedPnL: {}", 
                    costBasis.amount(), realizedPnL.amount());
            
            // 6. UpdatePositionCommand 발행
            UpdatePositionCommand command = UpdatePositionCommand.builder()
                    .portfolioId(portfolioId)
                    .orderId(OrderId.of("ORDER-FROM-BROKER-" + brokerOrderId)) // 임시 OrderId 생성
                    .symbol(symbol)
                    .side(OrderSide.SELL)
                    .quantity(executedQuantity)
                    .price(executedPrice)
                    .totalAmount(netReceived) // 세금/수수료 차감 후 실제 받는 금액
                    .build();
            
            // 7. CommandGateway로 포지션 업데이트 명령 발행
            commandGateway.send(command)
                    .thenRun(() -> {
                        log.info("✅ SELL position update completed - symbol: {}, remainingQty: {}, realizedPnL: {}", 
                                symbol.value(), remainingQuantity.value(), realizedPnL.amount());
                    })
                    .exceptionally(throwable -> {
                        log.error("🚨 Failed to update SELL position - portfolio: {}, symbol: {}", 
                                portfolioId.id(), symbol.value(), throwable);
                        return null;
                    });
            
        } catch (Exception e) {
            log.error("🚨 Failed to process SELL execution - portfolio: {}, symbol: {}", 
                    portfolioId.id(), symbol.value(), e);
        }
    }
    
    /**
     * 주문 상태 변경 이벤트 처리 - 취소된 주문에 대한 포트폴리오 상태 복원
     * 
     * @param event OrderStatusChangedEvent 주문 상태 변경 이벤트
     */
    @EventHandler
    public void on(OrderStatusChangedEvent event) {
        // 취소된 주문에 대한 처리
        if (event.newStatus() == OrderStatus.CANCELLED) {
            log.info("🔄 Processing order cancellation for portfolio sync - orderId: {}", 
                    event.orderId().value());
            
            try {
                // TODO: 취소된 주문에 대해 미체결 수량만큼 포트폴리오 상태 복원
                // 예를 들어, 부분 체결 후 나머지 수량 취소시 처리
                
                log.debug("📋 Order cancellation processed - orderId: {}", event.orderId().value());
                
            } catch (Exception e) {
                log.error("🚨 Failed to process order cancellation for portfolio sync - orderId: {}", 
                        event.orderId().value(), e);
            }
        }
    }
    
    /**
     * 포트폴리오 전체 가치 재계산
     * 
     * @param portfolioId 포트폴리오 ID
     * @return CompletableFuture<Money> 총 포트폴리오 가치
     */
    public CompletableFuture<Money> recalculatePortfolioValue(PortfolioId portfolioId) {
        log.info("🔄 Recalculating portfolio value - portfolioId: {}", portfolioId.id());
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                // TODO: 실제 구현에서는 모든 포지션의 현재가와 현금을 합산
                // 1. 현금 잔액 조회
                // 2. 모든 포지션의 시장가 기준 평가액 계산
                // 3. 총합 반환
                
                // 임시 구현
                return Money.of(new BigDecimal("10000000")); // 1천만원
                
            } catch (Exception e) {
                log.error("🚨 Failed to recalculate portfolio value - portfolioId: {}", 
                        portfolioId.id(), e);
                return Money.of(BigDecimal.ZERO);
            }
        });
    }
    
    /**
     * 포지션별 미실현 손익 계산
     * 
     * @param portfolioId 포트폴리오 ID
     * @param symbol 종목코드
     * @param currentPrice 현재가
     * @return 미실현 손익
     */
    public Money calculateUnrealizedPnL(PortfolioId portfolioId, Symbol symbol, Money currentPrice) {
        try {
            // TODO: PositionQueryService에서 해당 종목 포지션 조회
            // Quantity position = positionQueryService.getPosition(portfolioId, symbol);
            // Money averageCost = positionQueryService.getAveragePrice(portfolioId, symbol);
            // 
            // if (position.value() > 0) {
            //     Money currentValue = currentPrice.multiply(position.value());
            //     Money costBasis = averageCost.multiply(position.value());
            //     return currentValue.subtract(costBasis);
            // }
            
            // 임시 구현
            return Money.of(BigDecimal.ZERO);
            
        } catch (Exception e) {
            log.error("🚨 Failed to calculate unrealized P&L - portfolio: {}, symbol: {}", 
                    portfolioId.id(), symbol.value(), e);
            return Money.of(BigDecimal.ZERO);
        }
    }
}