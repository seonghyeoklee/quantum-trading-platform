package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.*;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import java.math.BigDecimal;

/**
 * 포지션 업데이트 명령 (주문 체결 후 포트폴리오 반영)
 */
@Value
@Builder
public class UpdatePositionCommand {
    @TargetAggregateIdentifier
    PortfolioId portfolioId;
    
    OrderId orderId;
    Symbol symbol;
    OrderSide side; // BUY 또는 SELL
    Quantity quantity;
    Money price;
    Money totalAmount; // 수수료 포함 총 거래 금액
    
    public void validate() {
        if (portfolioId == null) {
            throw new IllegalArgumentException("Portfolio ID cannot be null");
        }
        if (orderId == null) {
            throw new IllegalArgumentException("Order ID cannot be null");
        }
        if (symbol == null) {
            throw new IllegalArgumentException("Symbol cannot be null");
        }
        if (side == null) {
            throw new IllegalArgumentException("Order side cannot be null");
        }
        if (quantity == null || quantity.getValue() <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }
        if (price == null || price.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Price must be positive");
        }
        if (totalAmount == null || totalAmount.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Total amount must be positive");
        }
    }
}