package com.quantum.trading.platform.shared.value;

/**
 * 주문 방향 열거형
 * 
 * 매수/매도 구분
 */
public enum OrderSide {
    /**
     * 매수 주문
     */
    BUY("매수", "01"),
    
    /**
     * 매도 주문
     */
    SELL("매도", "02");
    
    private final String displayName;
    private final String kisCode; // 한국투자증권 API 코드
    
    OrderSide(String displayName, String kisCode) {
        this.displayName = displayName;
        this.kisCode = kisCode;
    }
    
    public String getDisplayName() {
        return displayName;
    }
    
    public String getKisCode() {
        return kisCode;
    }
    
    /**
     * KIS API 코드로부터 OrderSide 조회
     */
    public static OrderSide fromKisCode(String kisCode) {
        for (OrderSide side : values()) {
            if (side.kisCode.equals(kisCode)) {
                return side;
            }
        }
        throw new IllegalArgumentException("Unknown KIS code: " + kisCode);
    }
    
    /**
     * 반대 방향 반환
     */
    public OrderSide opposite() {
        return this == BUY ? SELL : BUY;
    }
    
    /**
     * 매수 주문인지 확인
     */
    public boolean isBuy() {
        return this == BUY;
    }
    
    /**
     * 매도 주문인지 확인
     */
    public boolean isSell() {
        return this == SELL;
    }
}