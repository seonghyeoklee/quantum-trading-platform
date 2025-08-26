package com.quantum.trading.platform.shared.value;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;

class MoneyTest {
    
    @Test
    void shouldCreateKrwMoney() {
        Money money = Money.ofKrw(BigDecimal.valueOf(10000));
        
        assertEquals(BigDecimal.valueOf(10000), money.amount());
        assertEquals("KRW", money.currency().getCurrencyCode());
    }
    
    @Test
    void shouldCreateZeroKrw() {
        Money money = Money.zeroKrw();
        
        assertTrue(money.isZero());
        assertEquals("KRW", money.currency().getCurrencyCode());
    }
    
    @Test
    void shouldAddSameCurrency() {
        Money money1 = Money.ofKrw(10000);
        Money money2 = Money.ofKrw(5000);
        
        Money result = money1.add(money2);
        
        assertEquals(BigDecimal.valueOf(15000), result.amount());
    }
    
    @Test
    void shouldSubtractSameCurrency() {
        Money money1 = Money.ofKrw(10000);
        Money money2 = Money.ofKrw(3000);
        
        Money result = money1.subtract(money2);
        
        assertEquals(BigDecimal.valueOf(7000), result.amount());
    }
    
    @Test
    void shouldThrowExceptionWhenSubtractResultsInNegative() {
        Money money1 = Money.ofKrw(5000);
        Money money2 = Money.ofKrw(10000);
        
        assertThrows(IllegalArgumentException.class, () -> money1.subtract(money2));
    }
    
    @Test
    void shouldMultiplyByInteger() {
        Money money = Money.ofKrw(1000);
        
        Money result = money.multiply(5);
        
        assertEquals(BigDecimal.valueOf(5000), result.amount());
    }
    
    @Test
    void shouldCompareMoney() {
        Money money1 = Money.ofKrw(10000);
        Money money2 = Money.ofKrw(5000);
        
        assertTrue(money1.isGreaterThan(money2));
        assertTrue(money2.isLessThan(money1));
        assertTrue(money1.isGreaterThanOrEqual(money2));
    }
    
    @Test
    void shouldThrowExceptionWhenNegativeAmount() {
        assertThrows(IllegalArgumentException.class, 
            () -> Money.ofKrw(BigDecimal.valueOf(-1000)));
    }
    
    @Test
    void shouldThrowExceptionWhenAddingDifferentCurrencies() {
        Money krw = Money.ofKrw(10000);
        Money usd = Money.of(BigDecimal.valueOf(100), "USD");
        
        assertThrows(IllegalArgumentException.class, () -> krw.add(usd));
    }
}