package com.quantum.trading.platform.shared.value;

/**
 * 주문 유형 열거형
 * 
 * 한국 주식 거래에서 사용되는 주문 유형들
 */
public enum OrderType {
    /**
     * 시장가 주문 - 현재 시장 가격으로 즉시 체결
     */
    MARKET("시장가"),
    
    /**
     * 지정가 주문 - 지정한 가격으로 주문
     */
    LIMIT("지정가"),
    
    /**
     * 조건부 지정가 - 최유리 지정가
     */
    CONDITIONAL_LIMIT("조건부지정가"),
    
    /**
     * 최유리 지정가 - 매수는 최우선 매도호가, 매도는 최우선 매수호가
     */
    BEST_LIMIT("최유리지정가"),
    
    /**
     * 장전 시간외 거래
     */
    PRE_MARKET("장전시간외"),
    
    /**
     * 장후 시간외 거래
     */
    AFTER_MARKET("장후시간외");
    
    private final String displayName;
    
    OrderType(String displayName) {
        this.displayName = displayName;
    }
    
    public String getDisplayName() {
        return displayName;
    }
    
    /**
     * 가격 지정이 필요한 주문 유형인지 확인
     */
    public boolean requiresPrice() {
        return this == LIMIT || this == CONDITIONAL_LIMIT || this == PRE_MARKET || this == AFTER_MARKET;
    }
    
    /**
     * 시장 시간 중에만 가능한 주문 유형인지 확인
     */
    public boolean isMarketHoursOnly() {
        return this == MARKET || this == LIMIT || this == CONDITIONAL_LIMIT || this == BEST_LIMIT;
    }
    
    /**
     * 시간외 거래 주문인지 확인
     */
    public boolean isAfterHoursOrder() {
        return this == PRE_MARKET || this == AFTER_MARKET;
    }
}