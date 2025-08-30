package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.*;

import java.time.Instant;

/**
 * 포지션 업데이트 이벤트
 */
public record PositionUpdatedEvent(
    PortfolioId portfolioId,
    OrderId orderId,
    Symbol symbol,
    OrderSide side,
    Quantity quantity,
    Money price,
    Money totalAmount,
    Position newPosition, // 업데이트된 포지션 정보
    Money newCashBalance, // 업데이트된 현금 잔액
    Instant timestamp
) {
    
    /**
     * Builder pattern support for test compatibility
     */
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private PortfolioId portfolioId;
        private OrderId orderId;
        private Symbol symbol;
        private OrderSide side;
        private Quantity quantity;
        private Money price;
        private Money totalAmount;
        private Position newPosition;
        private Money newCashBalance;
        private Instant timestamp;
        
        public Builder portfolioId(PortfolioId portfolioId) {
            this.portfolioId = portfolioId;
            return this;
        }
        
        public Builder orderId(OrderId orderId) {
            this.orderId = orderId;
            return this;
        }
        
        public Builder symbol(Symbol symbol) {
            this.symbol = symbol;
            return this;
        }
        
        public Builder side(OrderSide side) {
            this.side = side;
            return this;
        }
        
        public Builder quantity(Quantity quantity) {
            this.quantity = quantity;
            return this;
        }
        
        public Builder price(Money price) {
            this.price = price;
            return this;
        }
        
        public Builder totalAmount(Money totalAmount) {
            this.totalAmount = totalAmount;
            return this;
        }
        
        public Builder newPosition(Position newPosition) {
            this.newPosition = newPosition;
            return this;
        }
        
        public Builder newCashBalance(Money newCashBalance) {
            this.newCashBalance = newCashBalance;
            return this;
        }
        
        public Builder timestamp(Instant timestamp) {
            this.timestamp = timestamp;
            return this;
        }
        
        public PositionUpdatedEvent build() {
            if (timestamp == null) {
                timestamp = Instant.now();
            }
            return new PositionUpdatedEvent(portfolioId, orderId, symbol, side, quantity, price, totalAmount, newPosition, newCashBalance, timestamp);
        }
    }
}