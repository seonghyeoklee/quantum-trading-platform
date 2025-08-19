package com.quantum.trading.platform.command.aggregate;

import com.quantum.trading.platform.shared.command.*;
import com.quantum.trading.platform.shared.event.*;
import com.quantum.trading.platform.shared.value.*;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateLifecycle;
import org.axonframework.spring.stereotype.Aggregate;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * 포트폴리오 Aggregate
 * 
 * 사용자의 현금 잔액과 주식 보유 현황을 관리하는 핵심 집계
 */
@Aggregate
@NoArgsConstructor
@Slf4j
public class Portfolio {
    
    @AggregateIdentifier
    private PortfolioId portfolioId;
    
    private UserId userId;
    private Money cashBalance;
    private Map<Symbol, Position> positions;
    
    /**
     * 포트폴리오 생성 Command Handler
     */
    @CommandHandler
    public Portfolio(CreatePortfolioCommand command) {
        log.info("Creating portfolio: {}", command);
        
        command.validate();
        
        AggregateLifecycle.apply(PortfolioCreatedEvent.builder()
                .portfolioId(command.getPortfolioId())
                .userId(command.getUserId())
                .initialCash(command.getInitialCash())
                .timestamp(Instant.now())
                .build());
    }
    
    /**
     * 현금 입금 Command Handler
     */
    @CommandHandler
    public void handle(DepositCashCommand command) {
        log.info("Depositing cash to portfolio {}: {}", portfolioId, command.getAmount());
        
        command.validate();
        
        Money newBalance = Money.ofKrw(
                cashBalance.getAmount().add(command.getAmount().getAmount())
        );
        
        AggregateLifecycle.apply(CashDepositedEvent.builder()
                .portfolioId(portfolioId)
                .amount(command.getAmount())
                .newCashBalance(newBalance)
                .description(command.getDescription())
                .timestamp(Instant.now())
                .build());
    }
    
    /**
     * 포지션 업데이트 Command Handler (주문 체결 후)
     */
    @CommandHandler
    public void handle(UpdatePositionCommand command) {
        log.info("Updating position in portfolio {}: {} {} {} @ {}", 
                portfolioId, command.getSide(), command.getQuantity(), 
                command.getSymbol(), command.getPrice());
        
        command.validate();
        
        if (command.getSide() == OrderSide.BUY) {
            handleBuyOrder(command);
        } else {
            handleSellOrder(command);
        }
    }
    
    private void handleBuyOrder(UpdatePositionCommand command) {
        // 매수 시 현금 잔액 확인
        if (cashBalance.getAmount().compareTo(command.getTotalAmount().getAmount()) < 0) {
            throw new IllegalStateException("Insufficient cash balance for purchase");
        }
        
        Position newPosition;
        Position existingPosition = positions.get(command.getSymbol());
        
        if (existingPosition == null || existingPosition.isEmpty()) {
            // 신규 포지션 생성
            newPosition = Position.create(command.getSymbol(), command.getQuantity(), command.getPrice());
        } else {
            // 기존 포지션에 수량 추가 (평균 단가 재계산)
            newPosition = existingPosition.addQuantity(command.getQuantity(), command.getPrice());
        }
        
        // 현금 잔액 차감
        Money newCashBalance = Money.ofKrw(
                cashBalance.getAmount().subtract(command.getTotalAmount().getAmount())
        );
        
        AggregateLifecycle.apply(PositionUpdatedEvent.builder()
                .portfolioId(portfolioId)
                .orderId(command.getOrderId())
                .symbol(command.getSymbol())
                .side(command.getSide())
                .quantity(command.getQuantity())
                .price(command.getPrice())
                .totalAmount(command.getTotalAmount())
                .newPosition(newPosition)
                .newCashBalance(newCashBalance)
                .timestamp(Instant.now())
                .build());
    }
    
    private void handleSellOrder(UpdatePositionCommand command) {
        Position existingPosition = positions.get(command.getSymbol());
        
        if (existingPosition == null || existingPosition.isEmpty()) {
            throw new IllegalStateException("No position to sell for symbol: " + command.getSymbol());
        }
        
        if (existingPosition.getQuantity().getValue() < command.getQuantity().getValue()) {
            throw new IllegalStateException("Insufficient quantity to sell");
        }
        
        // 포지션에서 수량 차감
        Position newPosition = existingPosition.reduceQuantity(command.getQuantity());
        
        // 현금 잔액 증가
        Money newCashBalance = Money.ofKrw(
                cashBalance.getAmount().add(command.getTotalAmount().getAmount())
        );
        
        AggregateLifecycle.apply(PositionUpdatedEvent.builder()
                .portfolioId(portfolioId)
                .orderId(command.getOrderId())
                .symbol(command.getSymbol())
                .side(command.getSide())
                .quantity(command.getQuantity())
                .price(command.getPrice())
                .totalAmount(command.getTotalAmount())
                .newPosition(newPosition)
                .newCashBalance(newCashBalance)
                .timestamp(Instant.now())
                .build());
    }
    
    /**
     * 포트폴리오 생성 Event Sourcing Handler
     */
    @EventSourcingHandler
    public void on(PortfolioCreatedEvent event) {
        this.portfolioId = event.getPortfolioId();
        this.userId = event.getUserId();
        this.cashBalance = event.getInitialCash();
        this.positions = new HashMap<>();
        
        log.debug("Portfolio created: {} for user: {}", portfolioId, userId);
    }
    
    /**
     * 현금 입금 Event Sourcing Handler
     */
    @EventSourcingHandler
    public void on(CashDepositedEvent event) {
        this.cashBalance = event.getNewCashBalance();
        
        log.debug("Cash deposited to portfolio {}: {}, new balance: {}", 
                portfolioId, event.getAmount(), cashBalance);
    }
    
    /**
     * 포지션 업데이트 Event Sourcing Handler
     */
    @EventSourcingHandler
    public void on(PositionUpdatedEvent event) {
        this.cashBalance = event.getNewCashBalance();
        
        if (event.getNewPosition().isEmpty()) {
            // 포지션이 비어있으면 제거
            this.positions.remove(event.getSymbol());
        } else {
            // 포지션 업데이트
            this.positions.put(event.getSymbol(), event.getNewPosition());
        }
        
        log.debug("Position updated in portfolio {}: {} {}, new cash balance: {}", 
                portfolioId, event.getSide(), event.getSymbol(), cashBalance);
    }
    
    // Getters for testing
    public PortfolioId getPortfolioId() {
        return portfolioId;
    }
    
    public UserId getUserId() {
        return userId;
    }
    
    public Money getCashBalance() {
        return cashBalance;
    }
    
    public Map<Symbol, Position> getPositions() {
        return new HashMap<>(positions);
    }
    
    public Position getPosition(Symbol symbol) {
        return positions.get(symbol);
    }
    
    /**
     * 총 포트폴리오 가치 계산 (현금 + 주식 평가액)
     */
    public Money calculateTotalValue(Map<Symbol, Money> currentPrices) {
        BigDecimal totalValue = cashBalance.getAmount();
        
        for (Position position : positions.values()) {
            Money currentPrice = currentPrices.get(position.getSymbol());
            if (currentPrice != null) {
                totalValue = totalValue.add(
                        position.calculateMarketValue(currentPrice).getAmount()
                );
            }
        }
        
        return Money.ofKrw(totalValue);
    }
}