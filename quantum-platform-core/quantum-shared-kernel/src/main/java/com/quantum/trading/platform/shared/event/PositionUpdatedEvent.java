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
) {}