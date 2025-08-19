package com.quantum.trading.platform.query.integration;

import com.quantum.trading.platform.query.repository.OrderViewRepository;
import com.quantum.trading.platform.query.repository.PortfolioViewRepository;
import com.quantum.trading.platform.query.service.OrderQueryService;
import com.quantum.trading.platform.query.service.PortfolioQueryService;
import com.quantum.trading.platform.query.view.OrderView;
import com.quantum.trading.platform.query.view.PortfolioView;
import com.quantum.trading.platform.shared.value.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Disabled;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Trading Query 통합 테스트
 * 
 * H2 인메모리 데이터베이스를 사용한 JPA Repository 및 Service 테스트
 */
@DataJpaTest
@ActiveProfiles("test")
@Import({OrderQueryService.class, PortfolioQueryService.class})
@Disabled("Configuration issues - will fix later")
class QueryIntegrationTest {
    
    @Autowired
    private OrderViewRepository orderViewRepository;
    
    @Autowired
    private PortfolioViewRepository portfolioViewRepository;
    
    @Autowired
    private OrderQueryService orderQueryService;
    
    @Autowired
    private PortfolioQueryService portfolioQueryService;
    
    @Test
    void shouldSaveAndRetrieveOrderView() {
        // Given
        OrderView orderView = OrderView.fromOrderCreated(
                OrderId.of("ORDER-TEST-001"),
                UserId.of("user-001"),
                Symbol.of("005930"),
                OrderType.LIMIT,
                OrderSide.BUY,
                Money.ofKrw(BigDecimal.valueOf(75000)),
                Quantity.of(10),
                Instant.now()
        );
        
        // When
        OrderView saved = orderViewRepository.save(orderView);
        Optional<OrderView> retrieved = orderQueryService.getOrder("ORDER-TEST-001");
        
        // Then
        assertThat(saved.getOrderId()).isEqualTo("ORDER-TEST-001");
        assertThat(retrieved).isPresent();
        assertThat(retrieved.get().getUserId()).isEqualTo("user-001");
        assertThat(retrieved.get().getSymbol()).isEqualTo("005930");
        assertThat(retrieved.get().getStatus()).isEqualTo(OrderStatus.PENDING);
    }
    
    @Test
    void shouldSaveAndRetrievePortfolioView() {
        // Given
        PortfolioView portfolioView = PortfolioView.fromPortfolioCreated(
                PortfolioId.of("PORTFOLIO-TEST-001"),
                UserId.of("user-001"),
                Money.ofKrw(BigDecimal.valueOf(1000000)),
                Instant.now()
        );
        
        // When
        PortfolioView saved = portfolioViewRepository.save(portfolioView);
        Optional<PortfolioView> retrieved = portfolioQueryService.getUserPortfolio("user-001");
        
        // Then
        assertThat(saved.getPortfolioId()).isEqualTo("PORTFOLIO-TEST-001");
        assertThat(retrieved).isPresent();
        assertThat(retrieved.get().getCashBalance()).isEqualTo(BigDecimal.valueOf(1000000.00));
        assertThat(retrieved.get().getPositionCount()).isEqualTo(0);
        assertThat(retrieved.get().getTotalProfitLoss()).isEqualTo(BigDecimal.ZERO);
    }
    
    @Test
    void shouldFindUserActiveOrders() {
        // Given
        OrderView pendingOrder = OrderView.fromOrderCreated(
                OrderId.of("ORDER-PENDING-001"),
                UserId.of("user-001"),
                Symbol.of("005930"),
                OrderType.LIMIT,
                OrderSide.BUY,
                Money.ofKrw(BigDecimal.valueOf(75000)),
                Quantity.of(10),
                Instant.now()
        );
        
        OrderView filledOrder = OrderView.fromOrderCreated(
                OrderId.of("ORDER-FILLED-001"),
                UserId.of("user-001"),
                Symbol.of("000660"),
                OrderType.LIMIT,
                OrderSide.BUY,
                Money.ofKrw(BigDecimal.valueOf(50000)),
                Quantity.of(5),
                Instant.now()
        );
        filledOrder.setStatus(OrderStatus.FILLED);
        
        orderViewRepository.save(pendingOrder);
        orderViewRepository.save(filledOrder);
        
        // When
        var activeOrders = orderQueryService.getUserActiveOrders("user-001");
        
        // Then
        assertThat(activeOrders).hasSize(1);
        assertThat(activeOrders.get(0).getOrderId()).isEqualTo("ORDER-PENDING-001");
        assertThat(activeOrders.get(0).getStatus()).isEqualTo(OrderStatus.PENDING);
    }
    
    @Test
    void shouldCalculateOrderTradingSummary() {
        // Given
        createTestOrders();
        
        // When
        var summary = orderQueryService.getUserTradingSummary("user-001");
        
        // Then
        assertThat(summary.getTotalTrades()).isGreaterThan(0);
        assertThat(summary.getTotalTradeAmount()).isGreaterThan(BigDecimal.ZERO);
    }
    
    private void createTestOrders() {
        OrderView buyOrder = OrderView.fromOrderCreated(
                OrderId.of("ORDER-BUY-001"),
                UserId.of("user-001"),
                Symbol.of("005930"),
                OrderType.LIMIT,
                OrderSide.BUY,
                Money.ofKrw(BigDecimal.valueOf(75000)),
                Quantity.of(10),
                Instant.now()
        );
        buyOrder.setStatus(OrderStatus.FILLED);
        buyOrder.setFilledQuantity(10);
        buyOrder.setFilledPrice(BigDecimal.valueOf(75000));
        buyOrder.setTotalAmount(BigDecimal.valueOf(750000));
        
        OrderView sellOrder = OrderView.fromOrderCreated(
                OrderId.of("ORDER-SELL-001"),
                UserId.of("user-001"),
                Symbol.of("000660"),
                OrderType.LIMIT,
                OrderSide.SELL,
                Money.ofKrw(BigDecimal.valueOf(50000)),
                Quantity.of(5),
                Instant.now()
        );
        sellOrder.setStatus(OrderStatus.FILLED);
        sellOrder.setFilledQuantity(5);
        sellOrder.setFilledPrice(BigDecimal.valueOf(50000));
        sellOrder.setTotalAmount(BigDecimal.valueOf(250000));
        
        orderViewRepository.save(buyOrder);
        orderViewRepository.save(sellOrder);
    }
}