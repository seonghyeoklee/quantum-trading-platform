package com.quantum.backtest.domain;

/**
 * 거래 타입
 */
public enum TradeType {
    BUY("매수", "주식 매수"),
    SELL("매도", "주식 매도");

    private final String displayName;
    private final String description;

    TradeType(String displayName, String description) {
        this.displayName = displayName;
        this.description = description;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getDescription() {
        return description;
    }

    /**
     * 반대 거래 타입을 반환
     */
    public TradeType opposite() {
        return this == BUY ? SELL : BUY;
    }
}