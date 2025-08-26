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
                .portfolioId(command.portfolioId())
                .userId(command.userId())
                .initialCash(command.initialCash())
                .timestamp(Instant.now())
                .build());
    }
    
    /**
     * 현금 입금 Command Handler
     */
    @CommandHandler
    public void handle(DepositCashCommand command) {
        log.info("Depositing cash to portfolio {}: {}", portfolioId, command.amount());
        
        command.validate();
        
        Money newBalance = Money.ofKrw(
                cashBalance.amount().add(command.amount().amount())
        );
        
        AggregateLifecycle.apply(new CashDepositedEvent(
                portfolioId,
                command.amount(),
                newBalance,
                command.description(),
                Instant.now()));
    }
    
    /**
     * 포지션 업데이트 Command Handler (주문 체결 후)
     */
    @CommandHandler
    public void handle(UpdatePositionCommand command) {
        log.info("Updating position in portfolio {}: {} {} {} @ {}", 
                portfolioId, command.side(), command.quantity(), 
                command.symbol(), command.price());
        
        command.validate();
        
        if (command.side() == OrderSide.BUY) {
            handleBuyOrder(command);
        } else {
            handleSellOrder(command);
        }
    }
    
    private void handleBuyOrder(UpdatePositionCommand command) {
        // 매수 시 현금 잔액 확인
        if (cashBalance.amount().compareTo(command.totalAmount().amount()) < 0) {
            throw new IllegalStateException("Insufficient cash balance for purchase");
        }
        
        Position newPosition;
        Position existingPosition = positions.get(command.symbol());
        
        if (existingPosition == null || existingPosition.isEmpty()) {
            // 신규 포지션 생성
            newPosition = Position.create(command.symbol(), command.quantity(), command.price());
        } else {
            // 기존 포지션에 수량 추가 (평균 단가 재계산)
            newPosition = existingPosition.addQuantity(command.quantity(), command.price());
        }
        
        // 현금 잔액 차감
        Money newCashBalance = Money.ofKrw(
                cashBalance.amount().subtract(command.totalAmount().amount())
        );
        
        AggregateLifecycle.apply(new PositionUpdatedEvent(
                portfolioId,
                command.orderId(),
                command.symbol(),
                command.side(),
                command.quantity(),
                command.price(),
                command.totalAmount(),
                newPosition,
                newCashBalance,
                Instant.now()));
    }
    
    private void handleSellOrder(UpdatePositionCommand command) {
        Position existingPosition = positions.get(command.symbol());
        
        if (existingPosition == null || existingPosition.isEmpty()) {
            throw new IllegalStateException("No position to sell for symbol: " + command.symbol());
        }
        
        if (existingPosition.getQuantity().value() < command.quantity().value()) {
            throw new IllegalStateException("Insufficient quantity to sell");
        }
        
        // 포지션에서 수량 차감
        Position newPosition = existingPosition.reduceQuantity(command.quantity());
        
        // 현금 잔액 증가
        Money newCashBalance = Money.ofKrw(
                cashBalance.amount().add(command.totalAmount().amount())
        );
        
        AggregateLifecycle.apply(new PositionUpdatedEvent(
                portfolioId,
                command.orderId(),
                command.symbol(),
                command.side(),
                command.quantity(),
                command.price(),
                command.totalAmount(),
                newPosition,
                newCashBalance,
                Instant.now()));
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
        this.cashBalance = event.newCashBalance();
        
        log.debug("Cash deposited to portfolio {}: {}, new balance: {}", 
                portfolioId, event.amount(), cashBalance);
    }
    
    /**
     * 포지션 업데이트 Event Sourcing Handler
     */
    @EventSourcingHandler
    public void on(PositionUpdatedEvent event) {
        this.cashBalance = event.newCashBalance();
        
        if (event.newPosition().isEmpty()) {
            // 포지션이 비어있으면 제거
            this.positions.remove(event.symbol());
        } else {
            // 포지션 업데이트
            this.positions.put(event.symbol(), event.newPosition());
        }
        
        log.debug("Position updated in portfolio {}: {} {}, new cash balance: {}", 
                portfolioId, event.side(), event.symbol(), cashBalance);
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
        BigDecimal totalValue = cashBalance.amount();
        
        for (Position position : positions.values()) {
            Money currentPrice = currentPrices.get(position.getSymbol());
            if (currentPrice != null) {
                totalValue = totalValue.add(
                        position.calculateMarketValue(currentPrice).amount()
                );
            }
        }
        
        return Money.ofKrw(totalValue);
    }
}