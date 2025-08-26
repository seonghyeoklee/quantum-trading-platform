package com.quantum.trading.platform.command.aggregate;

import com.quantum.trading.platform.shared.command.CancelOrderCommand;
import com.quantum.trading.platform.shared.command.CreateOrderCommand;
import com.quantum.trading.platform.shared.command.SubmitOrderToBrokerCommand;
import com.quantum.trading.platform.shared.event.OrderCreatedEvent;
import com.quantum.trading.platform.shared.event.OrderStatusChangedEvent;
import com.quantum.trading.platform.shared.event.OrderSubmittedToBrokerEvent;
import com.quantum.trading.platform.shared.value.*;
import org.axonframework.test.aggregate.AggregateTestFixture;
import org.axonframework.test.aggregate.FixtureConfiguration;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

/**
 * TradingOrder Aggregate 테스트
 * 
 * Axon Framework Test Fixtures를 사용한 단위 테스트
 */
class TradingOrderTest {
    
    private FixtureConfiguration<TradingOrder> fixture;
    
    @BeforeEach
    void setUp() {
        fixture = new AggregateTestFixture<>(TradingOrder.class);
    }
    
    @Test
    void shouldCreateNewOrder() {
        OrderId orderId = OrderId.generate();
        UserId userId = UserId.of("user-001");
        Symbol symbol = Symbol.of("005930");
        Money price = Money.ofKrw(BigDecimal.valueOf(75000));
        Quantity quantity = Quantity.of(100);
        
        CreateOrderCommand command = CreateOrderCommand.builder()
                .orderId(orderId)
                .userId(userId)
                .symbol(symbol)
                .orderType(OrderType.LIMIT)
                .side(OrderSide.BUY)
                .price(price)
                .quantity(quantity)
                .build();
        
        fixture.givenNoPriorActivity()
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectState(state -> {
                    assert state.orderId().equals(orderId);
                    assert state.getStatus() == OrderStatus.PENDING;
                });
    }
    
    @Test
    void shouldSubmitOrderToBroker() {
        OrderId orderId = OrderId.generate();
        
        CreateOrderCommand createCommand = createSampleOrderCommand(orderId);
        
        SubmitOrderToBrokerCommand submitCommand = SubmitOrderToBrokerCommand.builder()
                .orderId(orderId)
                .brokerType("KIS")
                .accountNumber("12345678")
                .build();
        
        fixture.given(OrderCreatedEvent.builder()
                        .orderId(orderId)
                        .userId(UserId.of("user-001"))
                        .symbol(Symbol.of("005930"))
                        .orderType(OrderType.LIMIT)
                        .side(OrderSide.BUY)
                        .price(Money.ofKrw(75000))
                        .quantity(Quantity.of(100))
                        .timestamp(java.time.Instant.now())
                        .build())
                .when(submitCommand)
                .expectSuccessfulHandlerExecution()
                .expectState(state -> {
                    assert state.getStatus() == OrderStatus.SUBMITTED;
                });
    }
    
    @Test
    void shouldCancelOrder() {
        OrderId orderId = OrderId.generate();
        
        CancelOrderCommand cancelCommand = CancelOrderCommand.builder()
                .orderId(orderId)
                .reason("User requested cancellation")
                .build();
        
        fixture.given(OrderCreatedEvent.builder()
                        .orderId(orderId)
                        .userId(UserId.of("user-001"))
                        .symbol(Symbol.of("005930"))
                        .orderType(OrderType.LIMIT)
                        .side(OrderSide.BUY)
                        .price(Money.ofKrw(75000))
                        .quantity(Quantity.of(100))
                        .timestamp(java.time.Instant.now())
                        .build())
                .when(cancelCommand)
                .expectSuccessfulHandlerExecution()
                .expectState(state -> {
                    assert state.getStatus() == OrderStatus.CANCELLED;
                });
    }
    
    @Test
    void shouldRejectSubmissionWhenNotInPendingStatus() {
        OrderId orderId = OrderId.generate();
        
        SubmitOrderToBrokerCommand submitCommand = SubmitOrderToBrokerCommand.builder()
                .orderId(orderId)
                .brokerType("KIS")
                .accountNumber("12345678")
                .build();
        
        fixture.given(
                        OrderCreatedEvent.builder()
                                .orderId(orderId)
                                .userId(UserId.of("user-001"))
                                .symbol(Symbol.of("005930"))
                                .orderType(OrderType.LIMIT)
                                .side(OrderSide.BUY)
                                .price(Money.ofKrw(75000))
                                .quantity(Quantity.of(100))
                                .timestamp(java.time.Instant.now())
                                .build(),
                        OrderStatusChangedEvent.builder()
                                .orderId(orderId)
                                .previousStatus(OrderStatus.PENDING)
                                .newStatus(OrderStatus.CANCELLED)
                                .reason("Test cancellation")
                                .timestamp(java.time.Instant.now())
                                .build()
                )
                .when(submitCommand)
                .expectException(IllegalStateException.class);
    }
    
    @Test
    void shouldValidateCreateOrderCommand() {
        OrderId orderId = OrderId.generate();
        
        // 가격이 필요한 주문 유형인데 가격이 없는 경우
        CreateOrderCommand invalidCommand = CreateOrderCommand.builder()
                .orderId(orderId)
                .userId(UserId.of("user-001"))
                .symbol(Symbol.of("005930"))
                .orderType(OrderType.LIMIT)
                .side(OrderSide.BUY)
                .price(null) // 가격 누락
                .quantity(Quantity.of(100))
                .build();
        
        fixture.givenNoPriorActivity()
                .when(invalidCommand)
                .expectException(IllegalArgumentException.class);
    }
    
    private CreateOrderCommand createSampleOrderCommand(OrderId orderId) {
        return CreateOrderCommand.builder()
                .orderId(orderId)
                .userId(UserId.of("user-001"))
                .symbol(Symbol.of("005930"))
                .orderType(OrderType.LIMIT)
                .side(OrderSide.BUY)
                .price(Money.ofKrw(75000))
                .quantity(Quantity.of(100))
                .build();
    }
}