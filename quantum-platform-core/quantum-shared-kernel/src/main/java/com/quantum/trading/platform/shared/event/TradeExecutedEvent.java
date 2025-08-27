package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.*;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * 거래 체결 완료 이벤트
 * 
 * 거래 이력 저장이 완료된 후 알림 시스템으로 전달하기 위한 이벤트
 * 파이썬 어댑터나 슬랙 알림 모듈에서 구독하여 사용자에게 알림 전송
 */
public record TradeExecutedEvent(
    String tradeId,
    OrderId orderId,
    UserId userId,
    PortfolioId portfolioId,
    Symbol symbol,
    String symbolName,
    OrderSide side,
    Quantity executedQuantity,
    Money executedPrice,
    Money executedAmount,
    Money transactionFee,
    Money securitiesTax,
    Money netAmount,
    String brokerOrderId,
    String brokerTradeId,
    // P&L 정보 (매도시)
    Money averageCost,
    Money realizedPnL,
    BigDecimal realizedPnLRate,
    // 메타데이터
    Boolean isPartialFill,
    Integer fillSequence,
    String marketType,
    String currency,
    Instant executedAt,
    Instant timestamp
) {
    
    /**
     * Factory method - 매수 거래용
     */
    public static TradeExecutedEvent createBuyTrade(
            String tradeId,
            OrderId orderId,
            UserId userId,
            PortfolioId portfolioId,
            Symbol symbol,
            String symbolName,
            Quantity executedQuantity,
            Money executedPrice,
            Money executedAmount,
            Money transactionFee,
            String brokerOrderId,
            String brokerTradeId,
            Boolean isPartialFill,
            Integer fillSequence,
            Instant executedAt) {
        
        return new TradeExecutedEvent(
                tradeId,
                orderId,
                userId,
                portfolioId,
                symbol,
                symbolName,
                OrderSide.BUY,
                executedQuantity,
                executedPrice,
                executedAmount,
                transactionFee,
                Money.ofKrw(BigDecimal.ZERO), // 매수시 증권거래세 없음
                executedAmount.add(transactionFee), // 매수시 net amount
                brokerOrderId,
                brokerTradeId,
                null, // 매수시 평균단가 없음
                null, // 매수시 실현손익 없음
                null, // 매수시 수익률 없음
                isPartialFill,
                fillSequence,
                "KOSPI",
                "KRW",
                executedAt,
                Instant.now()
        );
    }
    
    /**
     * Factory method - 매도 거래용
     */
    public static TradeExecutedEvent createSellTrade(
            String tradeId,
            OrderId orderId,
            UserId userId,
            PortfolioId portfolioId,
            Symbol symbol,
            String symbolName,
            Quantity executedQuantity,
            Money executedPrice,
            Money executedAmount,
            Money transactionFee,
            Money securitiesTax,
            Money netAmount,
            String brokerOrderId,
            String brokerTradeId,
            Money averageCost,
            Money realizedPnL,
            BigDecimal realizedPnLRate,
            Boolean isPartialFill,
            Integer fillSequence,
            Instant executedAt) {
        
        return new TradeExecutedEvent(
                tradeId,
                orderId,
                userId,
                portfolioId,
                symbol,
                symbolName,
                OrderSide.SELL,
                executedQuantity,
                executedPrice,
                executedAmount,
                transactionFee,
                securitiesTax,
                netAmount,
                brokerOrderId,
                brokerTradeId,
                averageCost,
                realizedPnL,
                realizedPnLRate,
                isPartialFill,
                fillSequence,
                "KOSPI",
                "KRW",
                executedAt,
                Instant.now()
        );
    }
    
    /**
     * Builder pattern support
     */
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private String tradeId;
        private OrderId orderId;
        private UserId userId;
        private PortfolioId portfolioId;
        private Symbol symbol;
        private String symbolName;
        private OrderSide side;
        private Quantity executedQuantity;
        private Money executedPrice;
        private Money executedAmount;
        private Money transactionFee;
        private Money securitiesTax;
        private Money netAmount;
        private String brokerOrderId;
        private String brokerTradeId;
        private Money averageCost;
        private Money realizedPnL;
        private BigDecimal realizedPnLRate;
        private Boolean isPartialFill;
        private Integer fillSequence;
        private String marketType;
        private String currency;
        private Instant executedAt;
        private Instant timestamp;
        
        public Builder tradeId(String tradeId) {
            this.tradeId = tradeId;
            return this;
        }
        
        public Builder orderId(OrderId orderId) {
            this.orderId = orderId;
            return this;
        }
        
        public Builder userId(UserId userId) {
            this.userId = userId;
            return this;
        }
        
        public Builder portfolioId(PortfolioId portfolioId) {
            this.portfolioId = portfolioId;
            return this;
        }
        
        public Builder symbol(Symbol symbol) {
            this.symbol = symbol;
            return this;
        }
        
        public Builder symbolName(String symbolName) {
            this.symbolName = symbolName;
            return this;
        }
        
        public Builder side(OrderSide side) {
            this.side = side;
            return this;
        }
        
        public Builder executedQuantity(Quantity executedQuantity) {
            this.executedQuantity = executedQuantity;
            return this;
        }
        
        public Builder executedPrice(Money executedPrice) {
            this.executedPrice = executedPrice;
            return this;
        }
        
        public Builder executedAmount(Money executedAmount) {
            this.executedAmount = executedAmount;
            return this;
        }
        
        public Builder transactionFee(Money transactionFee) {
            this.transactionFee = transactionFee;
            return this;
        }
        
        public Builder securitiesTax(Money securitiesTax) {
            this.securitiesTax = securitiesTax;
            return this;
        }
        
        public Builder netAmount(Money netAmount) {
            this.netAmount = netAmount;
            return this;
        }
        
        public Builder brokerOrderId(String brokerOrderId) {
            this.brokerOrderId = brokerOrderId;
            return this;
        }
        
        public Builder brokerTradeId(String brokerTradeId) {
            this.brokerTradeId = brokerTradeId;
            return this;
        }
        
        public Builder averageCost(Money averageCost) {
            this.averageCost = averageCost;
            return this;
        }
        
        public Builder realizedPnL(Money realizedPnL) {
            this.realizedPnL = realizedPnL;
            return this;
        }
        
        public Builder realizedPnLRate(BigDecimal realizedPnLRate) {
            this.realizedPnLRate = realizedPnLRate;
            return this;
        }
        
        public Builder isPartialFill(Boolean isPartialFill) {
            this.isPartialFill = isPartialFill;
            return this;
        }
        
        public Builder fillSequence(Integer fillSequence) {
            this.fillSequence = fillSequence;
            return this;
        }
        
        public Builder marketType(String marketType) {
            this.marketType = marketType;
            return this;
        }
        
        public Builder currency(String currency) {
            this.currency = currency;
            return this;
        }
        
        public Builder executedAt(Instant executedAt) {
            this.executedAt = executedAt;
            return this;
        }
        
        public Builder timestamp(Instant timestamp) {
            this.timestamp = timestamp;
            return this;
        }
        
        public TradeExecutedEvent build() {
            if (timestamp == null) {
                timestamp = Instant.now();
            }
            return new TradeExecutedEvent(
                    tradeId, orderId, userId, portfolioId, symbol, symbolName, side,
                    executedQuantity, executedPrice, executedAmount, transactionFee,
                    securitiesTax, netAmount, brokerOrderId, brokerTradeId,
                    averageCost, realizedPnL, realizedPnLRate, isPartialFill,
                    fillSequence, marketType, currency, executedAt, timestamp
            );
        }
    }
    
    /**
     * 거래 요약 정보 생성 (알림용)
     */
    public String getTradeMessageSummary() {
        String action = side == OrderSide.BUY ? "매수" : "매도";
        String pnlInfo = "";
        
        if (realizedPnL != null && side == OrderSide.SELL) {
            String pnlSign = realizedPnL.amount().compareTo(BigDecimal.ZERO) >= 0 ? "+" : "";
            String pnlRateStr = realizedPnLRate != null ? String.format("%.2f%%", realizedPnLRate) : "";
            pnlInfo = String.format(" (손익: %s%s %s)", pnlSign, realizedPnL.amount(), pnlRateStr);
        }
        
        return String.format("%s %s %s주 @%s%s",
                action, symbolName != null ? symbolName : symbol.value(),
                executedQuantity.value(), executedPrice.amount(), pnlInfo);
    }
}