package com.quantum.trading.platform.query.service;

import com.quantum.trading.platform.query.repository.TradeViewRepository;
import com.quantum.trading.platform.query.view.TradeView;
import com.quantum.trading.platform.shared.value.OrderSide;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * 거래 이력 조회 서비스
 * 
 * TradeView 기반 거래 이력 및 통계 조회를 위한 CQRS Query Side 서비스
 */
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class TradeQueryService {
    
    private final TradeViewRepository tradeViewRepository;
    
    /**
     * 거래 상세 조회
     */
    public Optional<TradeView> getTradeById(String tradeId) {
        return tradeViewRepository.findById(tradeId);
    }
    
    /**
     * 주문 ID로 거래 조회
     */
    public Optional<TradeView> getTradeByOrderId(String orderId) {
        return tradeViewRepository.findByOrderId(orderId);
    }
    
    /**
     * 브로커 주문 ID로 거래 조회
     */
    public Optional<TradeView> getTradeByBrokerOrderId(String brokerOrderId) {
        return tradeViewRepository.findByBrokerOrderId(brokerOrderId);
    }
    
    /**
     * 브로커 거래 ID로 거래 조회
     */
    public Optional<TradeView> getTradeByBrokerTradeId(String brokerTradeId) {
        return tradeViewRepository.findByBrokerTradeId(brokerTradeId);
    }
    
    /**
     * 사용자별 거래 이력 조회 (페이징)
     */
    public Page<TradeView> getUserTrades(String userId, Pageable pageable) {
        return tradeViewRepository.findByUserIdOrderByExecutedAtDesc(userId, pageable);
    }
    
    /**
     * 사용자별 특정 종목 거래 이력 조회
     */
    public Page<TradeView> getUserTradesBySymbol(String userId, String symbol, Pageable pageable) {
        return tradeViewRepository.findByUserIdAndSymbolOrderByExecutedAtDesc(userId, symbol, pageable);
    }
    
    /**
     * 사용자별 매수/매도 거래 이력 조회
     */
    public Page<TradeView> getUserTradesBySide(String userId, OrderSide side, Pageable pageable) {
        return tradeViewRepository.findByUserIdAndSideOrderByExecutedAtDesc(userId, side, pageable);
    }
    
    /**
     * 포트폴리오별 거래 이력 조회
     */
    public Page<TradeView> getPortfolioTrades(String portfolioId, Pageable pageable) {
        return tradeViewRepository.findByPortfolioIdOrderByExecutedAtDesc(portfolioId, pageable);
    }
    
    /**
     * 포트폴리오별 특정 종목 거래 이력 조회
     */
    public Page<TradeView> getPortfolioTradesBySymbol(String portfolioId, String symbol, Pageable pageable) {
        return tradeViewRepository.findByPortfolioIdAndSymbolOrderByExecutedAtDesc(portfolioId, symbol, pageable);
    }
    
    /**
     * 기간별 거래 이력 조회
     */
    public Page<TradeView> getUserTradesByDateRange(String userId, LocalDateTime startDate, LocalDateTime endDate, Pageable pageable) {
        return tradeViewRepository.findByUserIdAndDateRange(userId, startDate, endDate, pageable);
    }
    
    /**
     * 포트폴리오 기간별 거래 이력 조회
     */
    public Page<TradeView> getPortfolioTradesByDateRange(String portfolioId, LocalDateTime startDate, LocalDateTime endDate, Pageable pageable) {
        return tradeViewRepository.findByPortfolioIdAndDateRange(portfolioId, startDate, endDate, pageable);
    }
    
    /**
     * 오늘 거래 이력 조회
     */
    public List<TradeView> getTodayTrades(String userId) {
        return tradeViewRepository.findTodayTradesByUserId(userId);
    }
    
    /**
     * 최근 거래 이력 조회 (제한)
     */
    public List<TradeView> getRecentTrades(String userId, int limit) {
        return tradeViewRepository.findRecentTradesByUserId(userId, limit);
    }
    
    /**
     * 사용자별 거래 통계
     */
    public Long getTotalTradeCount(String userId) {
        return tradeViewRepository.countByUserId(userId);
    }
    
    /**
     * 사용자별 매수/매도 거래 수
     */
    public Long getTradeCountBySide(String userId, OrderSide side) {
        return tradeViewRepository.countByUserIdAndSide(userId, side);
    }
    
    /**
     * 사용자별 총 거래 금액 (매수/매도)
     */
    public BigDecimal getTotalTradeAmount(String userId, OrderSide side) {
        BigDecimal result = tradeViewRepository.sumExecutedAmountByUserIdAndSide(userId, side);
        return result != null ? result : BigDecimal.ZERO;
    }
    
    /**
     * 사용자별 총 실현 손익
     */
    public BigDecimal getTotalRealizedPnL(String userId) {
        BigDecimal result = tradeViewRepository.sumRealizedPnLByUserId(userId);
        return result != null ? result : BigDecimal.ZERO;
    }
    
    /**
     * 사용자별 총 수수료 및 세금
     */
    public TradeFeesSummary getTotalFeesAndTaxes(String userId) {
        List<Object[]> results = tradeViewRepository.getTotalFeesAndTaxes(userId);
        
        if (results.isEmpty()) {
            return new TradeFeesSummary(BigDecimal.ZERO, BigDecimal.ZERO);
        }
        
        Object[] result = results.get(0);
        BigDecimal totalFees = result[0] != null ? (BigDecimal) result[0] : BigDecimal.ZERO;
        BigDecimal totalTaxes = result[1] != null ? (BigDecimal) result[1] : BigDecimal.ZERO;
        
        return new TradeFeesSummary(totalFees, totalTaxes);
    }
    
    /**
     * 종목별 거래 요약
     */
    public List<SymbolTradeSummary> getSymbolTradeSummary(String userId, OrderSide side) {
        List<Object[]> results = tradeViewRepository.getTradesSummaryBySymbol(userId, side);
        
        return results.stream()
                .map(result -> new SymbolTradeSummary(
                        (String) result[0],  // symbol
                        (Long) result[1],    // count
                        (Long) result[2],    // total quantity
                        (BigDecimal) result[3] // average price
                ))
                .collect(Collectors.toList());
    }
    
    /**
     * 월별 거래 통계
     */
    public List<MonthlyTradeStat> getMonthlyTradeStats(String userId) {
        List<Object[]> results = tradeViewRepository.getMonthlyTradeStats(userId);
        
        return results.stream()
                .map(result -> new MonthlyTradeStat(
                        (Integer) result[0], // year
                        (Integer) result[1], // month
                        (Long) result[2],    // trade count
                        (BigDecimal) result[3] // total amount
                ))
                .collect(Collectors.toList());
    }
    
    /**
     * 실현손익이 있는 거래 조회 (매도 거래만)
     */
    public List<TradeView> getProfitableTradesWithPnL(String userId, Pageable pageable) {
        return tradeViewRepository.findByUserIdAndRealizedPnLIsNotNullOrderByExecutedAtDesc(userId, pageable);
    }
    
    /**
     * 고수익 거래 조회 (최소 수익률 기준)
     */
    public List<TradeView> getProfitableTradesByMinRate(String userId, BigDecimal minRatePercent) {
        return tradeViewRepository.findProfitableTradesByMinRate(userId, minRatePercent);
    }
    
    /**
     * 부분 체결 거래 조회
     */
    public List<TradeView> getPartialFillTrades(String orderId) {
        return tradeViewRepository.findByOrderIdAndIsPartialFillTrueOrderByFillSequenceAsc(orderId);
    }
    
    /**
     * 종목의 최근 체결가 조회
     */
    public Optional<BigDecimal> getLatestExecutedPrice(String symbol) {
        return tradeViewRepository.findLatestExecutedPriceBySymbol(symbol);
    }
    
    /**
     * 사용자별 종합 거래 실적 요약
     */
    public TradingSummary getUserTradingSummary(String userId) {
        Long totalTrades = getTotalTradeCount(userId);
        Long buyTrades = getTradeCountBySide(userId, OrderSide.BUY);
        Long sellTrades = getTradeCountBySide(userId, OrderSide.SELL);
        
        BigDecimal totalBuyAmount = getTotalTradeAmount(userId, OrderSide.BUY);
        BigDecimal totalSellAmount = getTotalTradeAmount(userId, OrderSide.SELL);
        BigDecimal totalRealizedPnL = getTotalRealizedPnL(userId);
        
        TradeFeesSummary feesSummary = getTotalFeesAndTaxes(userId);
        
        return TradingSummary.builder()
                .totalTrades(totalTrades)
                .buyTrades(buyTrades)
                .sellTrades(sellTrades)
                .totalBuyAmount(totalBuyAmount)
                .totalSellAmount(totalSellAmount)
                .totalRealizedPnL(totalRealizedPnL)
                .totalFees(feesSummary.getTotalFees())
                .totalTaxes(feesSummary.getTotalTaxes())
                .netPnL(totalRealizedPnL.subtract(feesSummary.getTotalFees()).subtract(feesSummary.getTotalTaxes()))
                .build();
    }
    
    /**
     * 편의 메서드: 오늘부터 지정된 일수 이전까지의 거래 조회
     */
    public Page<TradeView> getRecentUserTrades(String userId, int days, Pageable pageable) {
        LocalDateTime endDate = LocalDateTime.now();
        LocalDateTime startDate = endDate.minusDays(days);
        return getUserTradesByDateRange(userId, startDate, endDate, pageable);
    }
    
    /**
     * 편의 메서드: 이번 달 거래 조회
     */
    public Page<TradeView> getThisMonthTrades(String userId) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime startOfMonth = now.withDayOfMonth(1).withHour(0).withMinute(0).withSecond(0).withNano(0);
        return getUserTradesByDateRange(userId, startOfMonth, now, PageRequest.of(0, 100));
    }
    
    /**
     * 편의 메서드: 이번 주 거래 조회
     */
    public Page<TradeView> getThisWeekTrades(String userId) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime startOfWeek = now.minusDays(now.getDayOfWeek().getValue() - 1)
                .withHour(0).withMinute(0).withSecond(0).withNano(0);
        return getUserTradesByDateRange(userId, startOfWeek, now, PageRequest.of(0, 100));
    }
    
    // DTO Classes
    
    /**
     * 수수료 및 세금 요약
     */
    public static class TradeFeesSummary {
        private final BigDecimal totalFees;
        private final BigDecimal totalTaxes;
        
        public TradeFeesSummary(BigDecimal totalFees, BigDecimal totalTaxes) {
            this.totalFees = totalFees;
            this.totalTaxes = totalTaxes;
        }
        
        public BigDecimal getTotalFees() { return totalFees; }
        public BigDecimal getTotalTaxes() { return totalTaxes; }
        public BigDecimal getTotalCost() { return totalFees.add(totalTaxes); }
    }
    
    /**
     * 종목별 거래 요약
     */
    public static class SymbolTradeSummary {
        private final String symbol;
        private final Long tradeCount;
        private final Long totalQuantity;
        private final BigDecimal averagePrice;
        
        public SymbolTradeSummary(String symbol, Long tradeCount, Long totalQuantity, BigDecimal averagePrice) {
            this.symbol = symbol;
            this.tradeCount = tradeCount;
            this.totalQuantity = totalQuantity;
            this.averagePrice = averagePrice;
        }
        
        public String getSymbol() { return symbol; }
        public Long getTradeCount() { return tradeCount; }
        public Long getTotalQuantity() { return totalQuantity; }
        public BigDecimal getAveragePrice() { return averagePrice; }
    }
    
    /**
     * 월별 거래 통계
     */
    public static class MonthlyTradeStat {
        private final Integer year;
        private final Integer month;
        private final Long tradeCount;
        private final BigDecimal totalAmount;
        
        public MonthlyTradeStat(Integer year, Integer month, Long tradeCount, BigDecimal totalAmount) {
            this.year = year;
            this.month = month;
            this.tradeCount = tradeCount;
            this.totalAmount = totalAmount;
        }
        
        public Integer getYear() { return year; }
        public Integer getMonth() { return month; }
        public Long getTradeCount() { return tradeCount; }
        public BigDecimal getTotalAmount() { return totalAmount; }
    }
    
    /**
     * 종합 거래 실적 요약
     */
    public static class TradingSummary {
        private final Long totalTrades;
        private final Long buyTrades;
        private final Long sellTrades;
        private final BigDecimal totalBuyAmount;
        private final BigDecimal totalSellAmount;
        private final BigDecimal totalRealizedPnL;
        private final BigDecimal totalFees;
        private final BigDecimal totalTaxes;
        private final BigDecimal netPnL;
        
        private TradingSummary(Long totalTrades, Long buyTrades, Long sellTrades,
                              BigDecimal totalBuyAmount, BigDecimal totalSellAmount,
                              BigDecimal totalRealizedPnL, BigDecimal totalFees,
                              BigDecimal totalTaxes, BigDecimal netPnL) {
            this.totalTrades = totalTrades;
            this.buyTrades = buyTrades;
            this.sellTrades = sellTrades;
            this.totalBuyAmount = totalBuyAmount;
            this.totalSellAmount = totalSellAmount;
            this.totalRealizedPnL = totalRealizedPnL;
            this.totalFees = totalFees;
            this.totalTaxes = totalTaxes;
            this.netPnL = netPnL;
        }
        
        public static TradingSummaryBuilder builder() {
            return new TradingSummaryBuilder();
        }
        
        // Getters
        public Long getTotalTrades() { return totalTrades; }
        public Long getBuyTrades() { return buyTrades; }
        public Long getSellTrades() { return sellTrades; }
        public BigDecimal getTotalBuyAmount() { return totalBuyAmount; }
        public BigDecimal getTotalSellAmount() { return totalSellAmount; }
        public BigDecimal getTotalRealizedPnL() { return totalRealizedPnL; }
        public BigDecimal getTotalFees() { return totalFees; }
        public BigDecimal getTotalTaxes() { return totalTaxes; }
        public BigDecimal getNetPnL() { return netPnL; }
        
        public static class TradingSummaryBuilder {
            private Long totalTrades;
            private Long buyTrades;
            private Long sellTrades;
            private BigDecimal totalBuyAmount;
            private BigDecimal totalSellAmount;
            private BigDecimal totalRealizedPnL;
            private BigDecimal totalFees;
            private BigDecimal totalTaxes;
            private BigDecimal netPnL;
            
            public TradingSummaryBuilder totalTrades(Long totalTrades) {
                this.totalTrades = totalTrades;
                return this;
            }
            
            public TradingSummaryBuilder buyTrades(Long buyTrades) {
                this.buyTrades = buyTrades;
                return this;
            }
            
            public TradingSummaryBuilder sellTrades(Long sellTrades) {
                this.sellTrades = sellTrades;
                return this;
            }
            
            public TradingSummaryBuilder totalBuyAmount(BigDecimal totalBuyAmount) {
                this.totalBuyAmount = totalBuyAmount;
                return this;
            }
            
            public TradingSummaryBuilder totalSellAmount(BigDecimal totalSellAmount) {
                this.totalSellAmount = totalSellAmount;
                return this;
            }
            
            public TradingSummaryBuilder totalRealizedPnL(BigDecimal totalRealizedPnL) {
                this.totalRealizedPnL = totalRealizedPnL;
                return this;
            }
            
            public TradingSummaryBuilder totalFees(BigDecimal totalFees) {
                this.totalFees = totalFees;
                return this;
            }
            
            public TradingSummaryBuilder totalTaxes(BigDecimal totalTaxes) {
                this.totalTaxes = totalTaxes;
                return this;
            }
            
            public TradingSummaryBuilder netPnL(BigDecimal netPnL) {
                this.netPnL = netPnL;
                return this;
            }
            
            public TradingSummary build() {
                return new TradingSummary(totalTrades, buyTrades, sellTrades,
                                        totalBuyAmount, totalSellAmount, totalRealizedPnL,
                                        totalFees, totalTaxes, netPnL);
            }
        }
    }
}