package com.quantum.trading.platform.command.aggregate;

import com.quantum.trading.platform.shared.command.*;
import com.quantum.trading.platform.shared.event.*;
import com.quantum.trading.platform.shared.value.*;
import org.axonframework.test.aggregate.AggregateTestFixture;
import org.axonframework.test.aggregate.FixtureConfiguration;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

/**
 * Portfolio Aggregate 테스트
 */
class PortfolioTest {
    
    private FixtureConfiguration<Portfolio> fixture;
    
    @BeforeEach
    void setUp() {
        fixture = new AggregateTestFixture<>(Portfolio.class);
    }
    
    @Test
    void shouldCreateNewPortfolio() {
        PortfolioId portfolioId = PortfolioId.generate();
        UserId userId = UserId.of("user-001");
        Money initialCash = Money.ofKrw(BigDecimal.valueOf(1000000));
        
        CreatePortfolioCommand command = CreatePortfolioCommand.builder()
                .portfolioId(portfolioId)
                .userId(userId)
                .initialCash(initialCash)
                .build();
        
        fixture.givenNoPriorActivity()
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectState(state -> {
                    assert state.getPortfolioId().equals(portfolioId);
                    assert state.getUserId().equals(userId);
                    assert state.getCashBalance().equals(initialCash);
                    assert state.getPositions().isEmpty();
                });
    }
    
    @Test
    void shouldDepositCash() {
        PortfolioId portfolioId = PortfolioId.generate();
        Money initialCash = Money.ofKrw(BigDecimal.valueOf(1000000));
        Money depositAmount = Money.ofKrw(BigDecimal.valueOf(500000));
        Money expectedBalance = Money.ofKrw(BigDecimal.valueOf(1500000));
        
        DepositCashCommand command = DepositCashCommand.builder()
                .portfolioId(portfolioId)
                .amount(depositAmount)
                .description("Test deposit")
                .build();
        
        fixture.given(PortfolioCreatedEvent.builder()
                        .portfolioId(portfolioId)
                        .userId(UserId.of("user-001"))
                        .initialCash(initialCash)
                        .timestamp(java.time.Instant.now())
                        .build())
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectState(state -> {
                    assert state.getCashBalance().equals(expectedBalance);
                });
    }
    
    @Test
    void shouldUpdatePositionOnBuyOrder() {
        PortfolioId portfolioId = PortfolioId.generate();
        Symbol symbol = Symbol.of("005930");
        Money initialCash = Money.ofKrw(BigDecimal.valueOf(1000000));
        Money buyPrice = Money.ofKrw(BigDecimal.valueOf(75000));
        Quantity buyQuantity = Quantity.of(10);
        Money totalAmount = Money.ofKrw(BigDecimal.valueOf(750000));
        
        UpdatePositionCommand command = UpdatePositionCommand.builder()
                .portfolioId(portfolioId)
                .orderId(OrderId.generate())
                .symbol(symbol)
                .side(OrderSide.BUY)
                .quantity(buyQuantity)
                .price(buyPrice)
                .totalAmount(totalAmount)
                .build();
        
        fixture.given(PortfolioCreatedEvent.builder()
                        .portfolioId(portfolioId)
                        .userId(UserId.of("user-001"))
                        .initialCash(initialCash)
                        .timestamp(java.time.Instant.now())
                        .build())
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectState(state -> {
                    assert state.getCashBalance().equals(Money.ofKrw(BigDecimal.valueOf(250000)));
                    assert state.getPosition(symbol) != null;
                    assert state.getPosition(symbol).getQuantity().equals(buyQuantity);
                    assert state.getPosition(symbol).getAveragePrice().equals(buyPrice);
                });
    }
    
    @Test
    void shouldUpdatePositionOnSellOrder() {
        PortfolioId portfolioId = PortfolioId.generate();
        Symbol symbol = Symbol.of("005930");
        Money initialCash = Money.ofKrw(BigDecimal.valueOf(250000));
        Quantity sellQuantity = Quantity.of(5);
        Money sellPrice = Money.ofKrw(BigDecimal.valueOf(80000));
        Money totalAmount = Money.ofKrw(BigDecimal.valueOf(400000));
        
        // 기존 포지션 생성
        Position existingPosition = Position.create(symbol, Quantity.of(10), Money.ofKrw(75000));
        
        UpdatePositionCommand command = UpdatePositionCommand.builder()
                .portfolioId(portfolioId)
                .orderId(OrderId.generate())
                .symbol(symbol)
                .side(OrderSide.SELL)
                .quantity(sellQuantity)
                .price(sellPrice)
                .totalAmount(totalAmount)
                .build();
        
        fixture.given(
                        PortfolioCreatedEvent.builder()
                                .portfolioId(portfolioId)
                                .userId(UserId.of("user-001"))
                                .initialCash(Money.ofKrw(BigDecimal.valueOf(1000000)))
                                .timestamp(java.time.Instant.now())
                                .build(),
                        PositionUpdatedEvent.builder()
                                .portfolioId(portfolioId)
                                .orderId(OrderId.generate())
                                .symbol(symbol)
                                .side(OrderSide.BUY)
                                .quantity(Quantity.of(10))
                                .price(Money.ofKrw(75000))
                                .totalAmount(Money.ofKrw(750000))
                                .newPosition(existingPosition)
                                .newCashBalance(initialCash)
                                .timestamp(java.time.Instant.now())
                                .build()
                )
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectState(state -> {
                    assert state.getCashBalance().equals(Money.ofKrw(BigDecimal.valueOf(650000)));
                    assert state.getPosition(symbol) != null;
                    assert state.getPosition(symbol).getQuantity().equals(Quantity.of(5));
                });
    }
    
    @Test
    void shouldRejectBuyWhenInsufficientCash() {
        PortfolioId portfolioId = PortfolioId.generate();
        Money initialCash = Money.ofKrw(BigDecimal.valueOf(100000));
        Money totalAmount = Money.ofKrw(BigDecimal.valueOf(150000)); // 잔액보다 큰 금액
        
        UpdatePositionCommand command = UpdatePositionCommand.builder()
                .portfolioId(portfolioId)
                .orderId(OrderId.generate())
                .symbol(Symbol.of("005930"))
                .side(OrderSide.BUY)
                .quantity(Quantity.of(10))
                .price(Money.ofKrw(15000))
                .totalAmount(totalAmount)
                .build();
        
        fixture.given(PortfolioCreatedEvent.builder()
                        .portfolioId(portfolioId)
                        .userId(UserId.of("user-001"))
                        .initialCash(initialCash)
                        .timestamp(java.time.Instant.now())
                        .build())
                .when(command)
                .expectException(IllegalStateException.class);
    }
    
    @Test
    void shouldRejectSellWhenNoPosition() {
        PortfolioId portfolioId = PortfolioId.generate();
        
        UpdatePositionCommand command = UpdatePositionCommand.builder()
                .portfolioId(portfolioId)
                .orderId(OrderId.generate())
                .symbol(Symbol.of("005930"))
                .side(OrderSide.SELL)
                .quantity(Quantity.of(10))
                .price(Money.ofKrw(75000))
                .totalAmount(Money.ofKrw(750000))
                .build();
        
        fixture.given(PortfolioCreatedEvent.builder()
                        .portfolioId(portfolioId)
                        .userId(UserId.of("user-001"))
                        .initialCash(Money.ofKrw(BigDecimal.valueOf(1000000)))
                        .timestamp(java.time.Instant.now())
                        .build())
                .when(command)
                .expectException(IllegalStateException.class);
    }
    
    @Test
    void shouldValidateCreatePortfolioCommand() {
        // null 포트폴리오 ID로 검증
        CreatePortfolioCommand invalidCommand = CreatePortfolioCommand.builder()
                .portfolioId(null)
                .userId(UserId.of("user-001"))
                .initialCash(Money.ofKrw(BigDecimal.valueOf(1000000)))
                .build();
        
        fixture.givenNoPriorActivity()
                .when(invalidCommand)
                .expectException(IllegalArgumentException.class);
    }
}