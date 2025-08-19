package com.quantum.trading.platform.shared.value;

import lombok.Value;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Currency;

/**
 * 금액 Value Object
 * 
 * 금융 계산에서 정확성을 위해 BigDecimal 사용
 * 한국 원화(KRW) 기본, 다른 통화 확장 가능
 */
@Value
public class Money {
    BigDecimal amount;
    Currency currency;
    
    private Money(BigDecimal amount, Currency currency) {
        if (amount == null) {
            throw new IllegalArgumentException("Amount cannot be null");
        }
        if (currency == null) {
            throw new IllegalArgumentException("Currency cannot be null");
        }
        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Amount cannot be negative: " + amount);
        }
        
        this.amount = amount.setScale(currency.getDefaultFractionDigits(), RoundingMode.HALF_UP);
        this.currency = currency;
    }
    
    /**
     * 한국 원화 생성
     */
    public static Money ofKrw(BigDecimal amount) {
        return new Money(amount, Currency.getInstance("KRW"));
    }
    
    public static Money ofKrw(long amount) {
        return ofKrw(BigDecimal.valueOf(amount));
    }
    
    public static Money ofKrw(double amount) {
        return ofKrw(BigDecimal.valueOf(amount));
    }
    
    /**
     * 임의 통화 생성
     */
    public static Money of(BigDecimal amount, Currency currency) {
        return new Money(amount, currency);
    }
    
    public static Money of(BigDecimal amount, String currencyCode) {
        return new Money(amount, Currency.getInstance(currencyCode));
    }
    
    /**
     * 0원 생성
     */
    public static Money zeroKrw() {
        return ofKrw(BigDecimal.ZERO);
    }
    
    /**
     * 금액 연산
     */
    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Cannot add different currencies: " + 
                this.currency + " and " + other.currency);
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }
    
    public Money subtract(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Cannot subtract different currencies: " + 
                this.currency + " and " + other.currency);
        }
        
        BigDecimal result = this.amount.subtract(other.amount);
        if (result.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Result cannot be negative: " + result);
        }
        
        return new Money(result, this.currency);
    }
    
    public Money multiply(BigDecimal multiplier) {
        return new Money(this.amount.multiply(multiplier), this.currency);
    }
    
    public Money multiply(int multiplier) {
        return multiply(BigDecimal.valueOf(multiplier));
    }
    
    /**
     * 비교 연산
     */
    public boolean isGreaterThan(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Cannot compare different currencies");
        }
        return this.amount.compareTo(other.amount) > 0;
    }
    
    public boolean isGreaterThanOrEqual(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Cannot compare different currencies");
        }
        return this.amount.compareTo(other.amount) >= 0;
    }
    
    public boolean isLessThan(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Cannot compare different currencies");
        }
        return this.amount.compareTo(other.amount) < 0;
    }
    
    public boolean isZero() {
        return this.amount.compareTo(BigDecimal.ZERO) == 0;
    }
    
    public boolean isPositive() {
        return this.amount.compareTo(BigDecimal.ZERO) > 0;
    }
    
    @Override
    public String toString() {
        return amount + " " + currency.getCurrencyCode();
    }
}