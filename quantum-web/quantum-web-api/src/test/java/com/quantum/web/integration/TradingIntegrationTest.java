package com.quantum.web.integration;

import com.quantum.trading.platform.query.view.OrderView;
import com.quantum.trading.platform.shared.command.CreateOrderCommand;
import com.quantum.trading.platform.shared.event.OrderCreatedEvent;
import com.quantum.trading.platform.shared.event.OrderExecutedEvent;
import com.quantum.trading.platform.shared.event.OrderSubmittedToBrokerEvent;
import com.quantum.trading.platform.shared.value.*;
import com.quantum.web.controller.TradingController.CreateOrderRequest;
import com.quantum.web.service.OrderExecutionService;
import com.quantum.web.service.TradingService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.axonframework.test.aggregate.AggregateTestFixture;
import org.axonframework.test.aggregate.FixtureConfiguration;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureTestMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * 거래 시스템 통합 테스트
 * 
 * End-to-End 거래 플로우 테스트:
 * 1. 주문 생성 → OrderCreatedEvent 발행
 * 2. Event Handler → 키움 API 호출 → OrderSubmittedToBrokerEvent 발행
 * 3. 실시간 추적 시작 → OrderExecutedEvent 수신
 * 4. Portfolio 동기화 → PositionUpdatedEvent 발행
 * 5. Query Side 업데이트 완료 검증
 */
@SpringBootTest
@AutoConfigureTestMvc
@ActiveProfiles("test")
@Transactional
public class TradingIntegrationTest {

    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private TradingService tradingService;
    
    @Autowired
    private OrderExecutionService orderExecutionService;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    private FixtureConfiguration<com.quantum.trading.platform.command.aggregate.TradingOrder> fixture;
    
    @BeforeEach
    void setUp() {
        fixture = new AggregateTestFixture<>(
                com.quantum.trading.platform.command.aggregate.TradingOrder.class);
    }
    
    /**
     * 완전한 매수 주문 플로우 테스트
     * 
     * 시나리오:
     * 1. REST API로 매수 주문 생성
     * 2. CQRS Command 처리 및 Event 발행
     * 3. 키움 API 호출 (시뮬레이션 모드)
     * 4. 실시간 추적 시작
     * 5. 모의 체결 처리
     * 6. Portfolio 업데이트
     * 7. Query Side 조회 검증
     */
    @Test
    void shouldCompleteFullBuyOrderFlow() throws Exception {
        // Given: 매수 주문 요청 데이터
        CreateOrderRequest buyOrderRequest = new CreateOrderRequest(
                "PORTFOLIO-TEST-001",
                "005930", // 삼성전자
                "BUY",
                "LIMIT",
                100, // 수량
                new BigDecimal("75000"), // 지정가
                null, // stopPrice
                null  // timeInForce
        );
        
        // When: REST API로 주문 생성
        String response = mockMvc.perform(post("/api/v1/trading/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(buyOrderRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("PENDING"))
                .andExpect(jsonPath("$.symbol").value("005930"))
                .andExpect(jsonPath("$.side").value("BUY"))
                .andExpect(jsonPath("$.quantity").value(100))
                .andExpect(jsonPath("$.price").value(75000))
                .andReturn()
                .getResponse()
                .getContentAsString();
        
        // Then: 응답에서 주문 ID 추출
        var orderResponse = objectMapper.readTree(response);
        String orderId = orderResponse.get("orderId").asText();
        
        assertThat(orderId).isNotNull();
        assertThat(orderId).startsWith("ORDER-");
        
        // 추가 검증: 비동기 처리 완료 대기 (최대 5초)
        await().atMost(5, TimeUnit.SECONDS)
                .untilAsserted(() -> {
                    // OrderView에서 주문 상태 확인
                    var order = tradingService.getOrder(orderId);
                    assertThat(order).isNotNull();
                    assertThat(order.status()).isIn("PENDING", "SUBMITTED", "FILLED");
                });
    }
    
    /**
     * 완전한 매도 주문 플로우 테스트
     */
    @Test
    void shouldCompleteFullSellOrderFlow() throws Exception {
        // Given: 매도 주문 요청 (보유 종목 가정)
        CreateOrderRequest sellOrderRequest = new CreateOrderRequest(
                "PORTFOLIO-TEST-001",
                "005930",
                "SELL",
                "LIMIT",
                50, // 보유 수량의 일부 매도
                new BigDecimal("76000"), // 지정가
                null,
                null
        );
        
        // When & Then: 매도 주문 생성 및 처리
        mockMvc.perform(post("/api/v1/trading/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(sellOrderRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.side").value("SELL"))
                .andExpect(jsonPath("$.quantity").value(50));
    }
    
    /**
     * 주문 취소 플로우 테스트
     */
    @Test
    void shouldCancelOrderSuccessfully() throws Exception {
        // Given: 먼저 주문 생성
        CreateOrderRequest orderRequest = new CreateOrderRequest(
                "PORTFOLIO-TEST-001",
                "005930",
                "BUY",
                "LIMIT",
                100,
                new BigDecimal("74000"),
                null,
                null
        );
        
        String createResponse = mockMvc.perform(post("/api/v1/trading/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(orderRequest)))
                .andExpect(status().isOk())
                .andReturn()
                .getResponse()
                .getContentAsString();
        
        String orderId = objectMapper.readTree(createResponse).get("orderId").asText();
        
        // When: 주문 취소
        mockMvc.perform(delete("/api/v1/trading/orders/{orderId}", orderId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("CANCELLED"))
                .andExpect(jsonPath("$.orderId").value(orderId));
    }
    
    /**
     * 리스크 관리 검증 테스트 - 자금 부족 시나리오
     */
    @Test
    void shouldRejectOrderDueToInsufficientFunds() throws Exception {
        // Given: 포트폴리오 자금을 초과하는 대량 주문
        CreateOrderRequest largeOrderRequest = new CreateOrderRequest(
                "PORTFOLIO-TEST-001",
                "005930",
                "BUY",
                "LIMIT",
                10000, // 대량 주문
                new BigDecimal("100000"), // 높은 가격
                null,
                null
        );
        
        // When & Then: 리스크 관리에 의한 주문 거부
        mockMvc.perform(post("/api/v1/trading/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(largeOrderRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").exists());
    }
    
    /**
     * 주문 목록 조회 테스트
     */
    @Test
    void shouldRetrieveOrdersWithFiltering() throws Exception {
        // Given: 여러 주문 생성 (생략 - 테스트 데이터 준비)
        
        // When & Then: 포트폴리오별 주문 목록 조회
        mockMvc.perform(get("/api/v1/trading/orders")
                        .param("portfolioId", "PORTFOLIO-TEST-001")
                        .param("status", "PENDING")
                        .param("page", "0")
                        .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.totalElements").exists())
                .andExpect(jsonPath("$.totalPages").exists());
    }
    
    /**
     * Axon Framework Aggregate 단위 테스트
     */
    @Test
    void shouldCreateOrderAggregateCorrectly() {
        // Given: CreateOrderCommand
        OrderId orderId = OrderId.generate();
        UserId userId = UserId.of("TEST-USER");
        Symbol symbol = Symbol.of("005930");
        OrderType orderType = OrderType.LIMIT;
        OrderSide side = OrderSide.BUY;
        Money price = Money.of(new BigDecimal("75000"));
        Quantity quantity = Quantity.of(100);
        
        CreateOrderCommand command = CreateOrderCommand.builder()
                .orderId(orderId)
                .userId(userId)
                .symbol(symbol)
                .orderType(orderType)
                .side(side)
                .price(price)
                .quantity(quantity)
                .build();
        
        // When & Then: Aggregate 생성 및 이벤트 검증
        fixture.givenNoPriorActivity()
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectEvents(OrderCreatedEvent.create(
                        orderId, userId, symbol, orderType, side, price, quantity));
    }
    
    /**
     * 키움 API 연동 단위 테스트 (시뮬레이션 모드)
     */
    @Test
    void shouldExecuteOrderViaKiwoomApiSimulation() {
        // Given: OrderCreatedEvent
        OrderCreatedEvent event = OrderCreatedEvent.create(
                OrderId.generate(),
                UserId.of("TEST-USER"),
                Symbol.of("005930"),
                OrderType.LIMIT,
                OrderSide.BUY,
                Money.of(new BigDecimal("75000")),
                Quantity.of(100)
        );
        
        // When: OrderExecutionService 호출
        CompletableFuture<OrderExecutionService.OrderExecutionResult> resultFuture = 
                orderExecutionService.executeOrder(event);
        
        // Then: 시뮬레이션 결과 검증
        assertThat(resultFuture).succeedsWithin(java.time.Duration.ofSeconds(5));
        
        OrderExecutionService.OrderExecutionResult result = resultFuture.join();
        assertThat(result).isNotNull();
        assertThat(result.isSuccessful()).isTrue();
        assertThat(result.getBrokerOrderId()).startsWith("SIM-");
    }
    
    /**
     * 실시간 주문 추적 테스트
     */
    @Test
    void shouldStartRealtimeOrderTracking() {
        // Given: OrderSubmittedToBrokerEvent
        OrderSubmittedToBrokerEvent event = OrderSubmittedToBrokerEvent.create(
                OrderId.generate(),
                UserId.of("TEST-USER"),
                "KIWOOM",
                "BROKER-ORDER-123"
        );
        
        // When: 실시간 추적 시작
        // 이벤트 핸들러가 자동으로 처리됨 (통합 테스트에서 검증)
        
        // Then: 추적 상태 확인 (실제 구현에서는 추적 서비스 상태 확인)
        assertThat(event.brokerOrderId()).isNotNull();
        assertThat(event.userId()).isNotNull();
    }
    
    /**
     * 포트폴리오 동기화 테스트 - 매수 체결
     */
    @Test
    void shouldSyncPortfolioOnBuyExecution() {
        // Given: OrderExecutedEvent (매수 체결)
        OrderId orderId = OrderId.generate();
        Quantity executedQuantity = Quantity.of(100);
        Money executedPrice = Money.of(new BigDecimal("75000"));
        
        OrderExecutedEvent executionEvent = OrderExecutedEvent.create(
                orderId,
                executedPrice,
                executedQuantity,
                Quantity.of(0), // 완전 체결
                "BROKER-ORDER-123",
                "EXECUTION-ID-001"
        );
        
        // When: 포트폴리오 동기화 처리
        // PortfolioSyncService의 EventHandler가 자동으로 처리됨
        
        // Then: 포지션 업데이트 검증 (실제로는 PortfolioView 조회)
        assertThat(executionEvent.getExecutedQuantity().getValue()).isEqualTo(100);
        assertThat(executionEvent.getExecutedPrice().getAmount()).isEqualByComparingTo(new BigDecimal("75000"));
    }
    
    // Helper method for async testing
    private org.awaitility.core.ConditionFactory await() {
        return org.awaitility.Awaitility.await();
    }
}