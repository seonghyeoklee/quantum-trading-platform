package com.quantum.trading.platform.shared.value;

/**
 * 수량 Value Object (Record 타입)
 * 
 * 주식 거래 수량을 나타내는 값 객체
 * 한국 주식은 1주 단위로 거래
 */
public record Quantity(int value) {
    
    public Quantity {
        if (value <= 0) {
            throw new IllegalArgumentException("Quantity must be positive: " + value);
        }
    }
    
    public static Quantity of(int value) {
        return new Quantity(value);
    }
    
    /**
     * 수량 연산
     */
    public Quantity add(Quantity other) {
        return new Quantity(this.value + other.value);
    }
    
    public Quantity subtract(Quantity other) {
        int result = this.value - other.value;
        if (result <= 0) {
            throw new IllegalArgumentException("Result quantity must be positive: " + result);
        }
        return new Quantity(result);
    }
    
    public Quantity multiply(int multiplier) {
        if (multiplier <= 0) {
            throw new IllegalArgumentException("Multiplier must be positive: " + multiplier);
        }
        return new Quantity(this.value * multiplier);
    }
    
    /**
     * 비교 연산
     */
    public boolean isGreaterThan(Quantity other) {
        return this.value > other.value;
    }
    
    public boolean isGreaterThanOrEqual(Quantity other) {
        return this.value >= other.value;
    }
    
    public boolean isLessThan(Quantity other) {
        return this.value < other.value;
    }
    
    public boolean isLessThanOrEqual(Quantity other) {
        return this.value <= other.value;
    }
    
    /**
     * 총 가격 계산
     */
    public Money calculateTotalPrice(Money unitPrice) {
        return unitPrice.multiply(this.value);
    }
    
    @Override
    public String toString() {
        return String.valueOf(value);
    }
}