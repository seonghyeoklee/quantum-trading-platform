package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.*;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

/**
 * 주문 생성 명령
 * 
 * 새로운 주문을 생성하기 위한 명령
 * Axon Framework의 Command 패턴 구현
 */
public record CreateOrderCommand(
    @TargetAggregateIdentifier
    OrderId orderId,
    UserId userId,
    Symbol symbol,
    OrderType orderType,
    OrderSide side,
    Money price,
    Quantity quantity
) {
    
    /**
     * 명령 검증
     */
    public void validate() {
        if (orderId == null) {
            throw new IllegalArgumentException("OrderId is required");
        }
        if (userId == null) {
            throw new IllegalArgumentException("UserId is required");
        }
        if (symbol == null) {
            throw new IllegalArgumentException("Symbol is required");
        }
        if (orderType == null) {
            throw new IllegalArgumentException("OrderType is required");
        }
        if (side == null) {
            throw new IllegalArgumentException("OrderSide is required");
        }
        if (quantity == null) {
            throw new IllegalArgumentException("Quantity is required");
        }
        
        // 가격이 필요한 주문 유형인데 가격이 없는 경우
        if (orderType.requiresPrice() && (price == null || price.isZero())) {
            throw new IllegalArgumentException("Price is required for order type: " + orderType);
        }
        
        // 시장가 주문인데 가격이 지정된 경우
        if (orderType == OrderType.MARKET && price != null && !price.isZero()) {
            throw new IllegalArgumentException("Price should not be specified for market order");
        }
    }
}