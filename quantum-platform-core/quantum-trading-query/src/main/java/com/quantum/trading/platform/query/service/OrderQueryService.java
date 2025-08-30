package com.quantum.trading.platform.query.service;

import com.quantum.trading.platform.query.repository.OrderViewRepository;
import com.quantum.trading.platform.query.view.OrderView;
import com.quantum.trading.platform.shared.value.OrderId;
import com.quantum.trading.platform.shared.value.OrderStatus;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * 주문 조회 서비스
 * 
 * CQRS Query Side 서비스
 */
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class OrderQueryService {
    
    private final OrderViewRepository orderViewRepository;
    
    /**
     * 주문 상세 조회
     */
    public Optional<OrderView> getOrder(String orderId) {
        return orderViewRepository.findById(orderId);
    }
    
    /**
     * 주문 상세 조회 (별칭)
     */
    public Optional<OrderView> getOrderById(String orderId) {
        return getOrder(orderId);
    }
    
    /**
     * 사용자별 주문 목록 조회 (페이징)
     */
    public Page<OrderView> getUserOrders(String userId, Pageable pageable) {
        return orderViewRepository.findByUserIdOrderByCreatedAtDesc(userId, pageable);
    }
    
    /**
     * 포트폴리오별 주문 목록 조회 (TradingService용)
     */
    public Page<OrderView> getOrdersByPortfolioId(String portfolioId, OrderStatus status, Pageable pageable) {
        if (status != null) {
            return orderViewRepository.findByPortfolioIdAndStatusOrderByCreatedAtDesc(portfolioId, status, pageable);
        } else {
            return orderViewRepository.findByPortfolioIdOrderByCreatedAtDesc(portfolioId, pageable);
        }
    }
    
    /**
     * 사용자별 활성 주문 조회
     */
    public List<OrderView> getUserActiveOrders(String userId) {
        return orderViewRepository.findActiveOrdersByUserId(userId);
    }
    
    /**
     * 사용자별 특정 상태 주문 조회
     */
    public List<OrderView> getUserOrdersByStatus(String userId, OrderStatus status) {
        return orderViewRepository.findByUserIdAndStatusOrderByCreatedAtDesc(userId, status);
    }
    
    /**
     * 사용자별 특정 종목 주문 조회
     */
    public List<OrderView> getUserOrdersBySymbol(String userId, String symbol) {
        return orderViewRepository.findByUserIdAndSymbolOrderByCreatedAtDesc(userId, symbol);
    }
    
    /**
     * 사용자별 체결된 주문 조회
     */
    public List<OrderView> getUserFilledOrders(String userId) {
        return orderViewRepository.findFilledOrdersByUserId(userId);
    }
    
    /**
     * 기간별 주문 조회
     */
    public List<OrderView> getUserOrdersByDateRange(String userId, LocalDate startDate, LocalDate endDate) {
        Instant startInstant = startDate.atStartOfDay().toInstant(ZoneOffset.UTC);
        Instant endInstant = endDate.plusDays(1).atStartOfDay().toInstant(ZoneOffset.UTC);
        
        return orderViewRepository.findByUserIdAndDateRange(userId, startInstant, endInstant);
    }
    
    /**
     * 기간별 주문 조회 (LocalDateTime 버전) - RiskManagementService용
     */
    public List<OrderView> findOrdersByUserIdAndDateRange(UserId userId, LocalDateTime startDateTime, LocalDateTime endDateTime) {
        Instant startInstant = startDateTime.toInstant(ZoneOffset.UTC);
        Instant endInstant = endDateTime.toInstant(ZoneOffset.UTC);
        
        return orderViewRepository.findByUserIdAndDateRange(userId.value(), startInstant, endInstant);
    }
    
    /**
     * OrderId로 주문 조회 (RiskManagementService용)
     */
    public OrderView findOrderById(OrderId orderId) {
        return orderViewRepository.findById(orderId.value()).orElse(null);
    }
    
    /**
     * 오늘 주문 조회
     */
    public List<OrderView> getTodayOrders(String userId) {
        return getUserOrdersByDateRange(userId, LocalDate.now(), LocalDate.now());
    }
    
    /**
     * 이번 주 주문 조회
     */
    public List<OrderView> getThisWeekOrders(String userId) {
        LocalDate today = LocalDate.now();
        LocalDate startOfWeek = today.minusDays(today.getDayOfWeek().getValue() - 1);
        return getUserOrdersByDateRange(userId, startOfWeek, today);
    }
    
    /**
     * 이번 달 주문 조회
     */
    public List<OrderView> getThisMonthOrders(String userId) {
        LocalDate today = LocalDate.now();
        LocalDate startOfMonth = today.withDayOfMonth(1);
        return getUserOrdersByDateRange(userId, startOfMonth, today);
    }
    
    /**
     * 특정 종목의 주문 목록 조회
     */
    public List<OrderView> getOrdersBySymbol(String symbol) {
        return orderViewRepository.findBySymbolOrderByCreatedAtDesc(symbol);
    }
    
    /**
     * 특정 브로커의 주문 조회
     */
    public List<OrderView> getOrdersByBroker(String brokerType) {
        return orderViewRepository.findByBrokerTypeOrderByCreatedAtDesc(brokerType);
    }
    
    /**
     * 브로커 주문 ID로 조회
     */
    public Optional<OrderView> getOrderByBrokerOrderId(String brokerOrderId) {
        return orderViewRepository.findByBrokerOrderId(brokerOrderId);
    }
    
    /**
     * 사용자별 주문 통계
     */
    public Map<OrderStatus, Long> getUserOrderStats(String userId) {
        List<Object[]> results = orderViewRepository.getOrderStatsByUserId(userId);
        
        return results.stream()
                .collect(Collectors.toMap(
                        result -> (OrderStatus) result[1],
                        result -> (Long) result[0]
                ));
    }
    
    /**
     * 미체결 주문 수 조회
     */
    public long getPendingOrderCount(String userId) {
        return orderViewRepository.countPendingOrdersByUserId(userId);
    }
    
    /**
     * 일별 주문 수 통계
     */
    public Map<LocalDate, Long> getDailyOrderStats(String userId, LocalDate startDate) {
        Instant startInstant = startDate.atStartOfDay().toInstant(ZoneOffset.UTC);
        List<Object[]> results = orderViewRepository.getDailyOrderStats(userId, startInstant);
        
        return results.stream()
                .collect(Collectors.toMap(
                        result -> (LocalDate) result[0],
                        result -> (Long) result[1]
                ));
    }
    
    /**
     * 특정 종목의 최근 체결가 조회
     */
    public List<BigDecimal> getRecentFilledPrices(String symbol, int limit) {
        return orderViewRepository.getRecentFilledPrices(
                symbol, 
                Pageable.ofSize(limit)
        );
    }
    
    /**
     * 거래 내역 조회 (TradingService용)
     */
    public Page<TradeView> getTradesByPortfolioId(String portfolioId, String symbol, 
                                                 String fromDate, String toDate, Pageable pageable) {
        // 실제로는 TradeView가 있어야 하지만, 임시로 OrderView를 활용
        // TODO: TradeView 구현 후 변경 필요
        
        if (symbol != null) {
            return orderViewRepository.findFilledOrdersByPortfolioIdAndSymbol(portfolioId, symbol, pageable)
                    .map(this::convertToTradeView);
        } else {
            return orderViewRepository.findFilledOrdersByPortfolioId(portfolioId, pageable)
                    .map(this::convertToTradeView);
        }
    }
    
    /**
     * OrderView를 TradeView로 임시 변환
     */
    private TradeView convertToTradeView(OrderView order) {
        return TradeView.builder()
                .tradeId("TRADE-" + order.getOrderId())
                .orderId(order.getOrderId())
                .portfolioId(order.getPortfolioId())
                .symbol(order.getSymbol())
                .side(order.getSide())
                .quantity(order.getFilledQuantity())
                .price(order.getAveragePrice())
                .amount(order.getTotalAmount())
                .executedAt(order.getUpdatedAt())
                .build();
    }
    
    /**
     * 임시 TradeView 클래스
     */
    @lombok.Builder
    public static class TradeView {
        private final String tradeId;
        private final String orderId;
        private final String portfolioId;
        private final String symbol;
        private final com.quantum.trading.platform.shared.value.OrderSide side;
        private final Integer quantity;
        private final java.math.BigDecimal price;
        private final java.math.BigDecimal amount;
        private final java.time.LocalDateTime executedAt;
        
        public String getTradeId() { return tradeId; }
        public String getOrderId() { return orderId; }
        public String getPortfolioId() { return portfolioId; }
        public String getSymbol() { return symbol; }
        public com.quantum.trading.platform.shared.value.OrderSide getSide() { return side; }
        public Integer getQuantity() { return quantity; }
        public java.math.BigDecimal getPrice() { return price; }
        public java.math.BigDecimal getAmount() { return amount; }
        public java.time.LocalDateTime getExecutedAt() { return executedAt; }
    }
    
    /**
     * 사용자별 매매 실적 요약
     */
    public OrderTradingSummary getUserTradingSummary(String userId) {
        List<OrderView> filledOrders = getUserFilledOrders(userId);
        
        long totalTrades = filledOrders.size();
        long buyTrades = filledOrders.stream()
                .filter(OrderView::isBuyOrder)
                .count();
        long sellTrades = totalTrades - buyTrades;
        
        BigDecimal totalTradeAmount = filledOrders.stream()
                .filter(order -> order.getTotalAmount() != null)
                .map(OrderView::getTotalAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        
        BigDecimal totalFees = filledOrders.stream()
                .filter(order -> order.getFee() != null)
                .map(OrderView::getFee)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        
        return OrderTradingSummary.builder()
                .totalTrades(totalTrades)
                .buyTrades(buyTrades)
                .sellTrades(sellTrades)
                .totalTradeAmount(totalTradeAmount)
                .totalFees(totalFees)
                .averageTradeAmount(totalTrades > 0 ? totalTradeAmount.divide(BigDecimal.valueOf(totalTrades), 2, BigDecimal.ROUND_HALF_UP) : BigDecimal.ZERO)
                .build();
    }
    
    /**
     * 주문 매매 실적 요약 DTO
     */
    public static class OrderTradingSummary {
        private final long totalTrades;
        private final long buyTrades;
        private final long sellTrades;
        private final BigDecimal totalTradeAmount;
        private final BigDecimal totalFees;
        private final BigDecimal averageTradeAmount;
        
        public static OrderTradingSummaryBuilder builder() {
            return new OrderTradingSummaryBuilder();
        }
        
        private OrderTradingSummary(long totalTrades, long buyTrades, long sellTrades, 
                                   BigDecimal totalTradeAmount, BigDecimal totalFees, BigDecimal averageTradeAmount) {
            this.totalTrades = totalTrades;
            this.buyTrades = buyTrades;
            this.sellTrades = sellTrades;
            this.totalTradeAmount = totalTradeAmount;
            this.totalFees = totalFees;
            this.averageTradeAmount = averageTradeAmount;
        }
        
        // Getters
        public long getTotalTrades() { return totalTrades; }
        public long getBuyTrades() { return buyTrades; }
        public long getSellTrades() { return sellTrades; }
        public BigDecimal getTotalTradeAmount() { return totalTradeAmount; }
        public BigDecimal getTotalFees() { return totalFees; }
        public BigDecimal getAverageTradeAmount() { return averageTradeAmount; }
        
        public static class OrderTradingSummaryBuilder {
            private long totalTrades;
            private long buyTrades;
            private long sellTrades;
            private BigDecimal totalTradeAmount;
            private BigDecimal totalFees;
            private BigDecimal averageTradeAmount;
            
            public OrderTradingSummaryBuilder totalTrades(long totalTrades) {
                this.totalTrades = totalTrades;
                return this;
            }
            
            public OrderTradingSummaryBuilder buyTrades(long buyTrades) {
                this.buyTrades = buyTrades;
                return this;
            }
            
            public OrderTradingSummaryBuilder sellTrades(long sellTrades) {
                this.sellTrades = sellTrades;
                return this;
            }
            
            public OrderTradingSummaryBuilder totalTradeAmount(BigDecimal totalTradeAmount) {
                this.totalTradeAmount = totalTradeAmount;
                return this;
            }
            
            public OrderTradingSummaryBuilder totalFees(BigDecimal totalFees) {
                this.totalFees = totalFees;
                return this;
            }
            
            public OrderTradingSummaryBuilder averageTradeAmount(BigDecimal averageTradeAmount) {
                this.averageTradeAmount = averageTradeAmount;
                return this;
            }
            
            public OrderTradingSummary build() {
                return new OrderTradingSummary(totalTrades, buyTrades, sellTrades, 
                                             totalTradeAmount, totalFees, averageTradeAmount);
            }
        }
    }
}