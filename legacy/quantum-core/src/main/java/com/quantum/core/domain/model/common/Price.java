package com.quantum.core.domain.model.common;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

/**
 * 가격 Value Object
 * 주식 가격 관련 비즈니스 로직과 검증을 캡슐화
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Embeddable
public class Price {

    @Column(name = "amount", precision = 19, scale = 2)
    private BigDecimal amount;

    @Column(name = "currency", length = 3)
    private String currency;

    private Price(BigDecimal amount, String currency) {
        validateAmount(amount);
        validateCurrency(currency);
        
        this.amount = amount.setScale(2, RoundingMode.HALF_UP);
        this.currency = currency.toUpperCase();
    }

    public static Price of(BigDecimal amount) {
        return new Price(amount, "KRW");
    }

    public static Price of(BigDecimal amount, String currency) {
        return new Price(amount, currency);
    }

    public static Price krw(BigDecimal amount) {
        return new Price(amount, "KRW");
    }

    public static Price usd(BigDecimal amount) {
        return new Price(amount, "USD");
    }

    public static Price zero() {
        return new Price(BigDecimal.ZERO, "KRW");
    }

    private void validateAmount(BigDecimal amount) {
        if (amount == null) {
            throw new IllegalArgumentException("가격은 필수입니다");
        }
        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("가격은 0 이상이어야 합니다");
        }
    }

    private void validateCurrency(String currency) {
        if (currency == null || currency.trim().isEmpty()) {
            throw new IllegalArgumentException("통화코드는 필수입니다");
        }
        if (currency.length() != 3) {
            throw new IllegalArgumentException("통화코드는 3자리여야 합니다");
        }
    }

    public Price add(Price other) {
        validateSameCurrency(other);
        return new Price(this.amount.add(other.amount), this.currency);
    }

    public Price subtract(Price other) {
        validateSameCurrency(other);
        return new Price(this.amount.subtract(other.amount), this.currency);
    }

    public Price multiply(BigDecimal multiplier) {
        return new Price(this.amount.multiply(multiplier), this.currency);
    }

    public Price divide(BigDecimal divisor) {
        if (divisor.compareTo(BigDecimal.ZERO) == 0) {
            throw new IllegalArgumentException("0으로 나눌 수 없습니다");
        }
        return new Price(this.amount.divide(divisor, 2, RoundingMode.HALF_UP), this.currency);
    }

    private void validateSameCurrency(Price other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("같은 통화끼리만 연산 가능합니다");
        }
    }

    public boolean isPositive() {
        return amount.compareTo(BigDecimal.ZERO) > 0;
    }

    public boolean isZero() {
        return amount.compareTo(BigDecimal.ZERO) == 0;
    }

    public boolean isGreaterThan(Price other) {
        validateSameCurrency(other);
        return amount.compareTo(other.amount) > 0;
    }

    public boolean isLessThan(Price other) {
        validateSameCurrency(other);
        return amount.compareTo(other.amount) < 0;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Price price = (Price) o;
        return Objects.equals(amount, price.amount) && Objects.equals(currency, price.currency);
    }

    @Override
    public int hashCode() {
        return Objects.hash(amount, currency);
    }

    @Override
    public String toString() {
        return String.format("%s %s", amount, currency);
    }
}