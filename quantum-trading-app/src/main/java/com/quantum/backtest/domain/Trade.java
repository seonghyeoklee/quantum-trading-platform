package com.quantum.backtest.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Objects;

/**
 * 거래 내역 Value Object
 */
public record Trade(
        LocalDateTime timestamp,    // 거래 시각
        TradeType type,            // 매수/매도
        BigDecimal price,          // 거래 가격
        int quantity,              // 거래 수량
        BigDecimal amount,         // 거래 금액
        String reason              // 거래 사유 (신호 설명)
) {

    public Trade {
        Objects.requireNonNull(timestamp, "Timestamp cannot be null");
        Objects.requireNonNull(type, "Trade type cannot be null");
        Objects.requireNonNull(price, "Price cannot be null");
        Objects.requireNonNull(amount, "Amount cannot be null");

        if (price.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Price must be positive");
        }
        if (quantity <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
    }

    /**
     * 거래 금액 계산을 위한 팩토리 메서드
     */
    public static Trade create(LocalDateTime timestamp, TradeType type,
                              BigDecimal price, int quantity, String reason) {
        BigDecimal amount = price.multiply(BigDecimal.valueOf(quantity));
        return new Trade(timestamp, type, price, quantity, amount, reason);
    }

    /**
     * 매수 거래인지 확인
     */
    public boolean isBuy() {
        return type == TradeType.BUY;
    }

    /**
     * 매도 거래인지 확인
     */
    public boolean isSell() {
        return type == TradeType.SELL;
    }

    /**
     * 거래 수수료를 적용한 실제 거래금액 계산 (0.015% 수수료)
     */
    public BigDecimal getActualAmount() {
        BigDecimal feeRate = new BigDecimal("0.00015"); // 0.015%
        BigDecimal fee = amount.multiply(feeRate);
        return isBuy() ? amount.add(fee) : amount.subtract(fee);
    }
}