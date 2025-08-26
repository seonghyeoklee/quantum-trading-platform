package com.quantum.trading.platform.shared.value;

import lombok.Value;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * 포지션 (특정 주식의 보유 수량과 평균 단가)
 */
@Value
public class Position {
    Symbol symbol;
    Quantity quantity;
    Money averagePrice;
    
    public static Position create(Symbol symbol, Quantity quantity, Money price) {
        if (symbol == null) {
            throw new IllegalArgumentException("Symbol cannot be null");
        }
        if (quantity == null || quantity.value() <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }
        if (price == null || price.amount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Price must be positive");
        }
        
        return new Position(symbol, quantity, price);
    }
    
    /**
     * 기존 포지션에 새로운 수량을 추가하고 평균 단가 재계산
     */
    public Position addQuantity(Quantity additionalQuantity, Money newPrice) {
        if (additionalQuantity.value() <= 0) {
            throw new IllegalArgumentException("Additional quantity must be positive");
        }
        
        // 기존 총 가치
        BigDecimal existingValue = averagePrice.amount()
                .multiply(BigDecimal.valueOf(quantity.value()));
        
        // 추가 구매 가치
        BigDecimal additionalValue = newPrice.amount()
                .multiply(BigDecimal.valueOf(additionalQuantity.value()));
        
        // 새로운 총 수량
        Quantity newQuantity = Quantity.of(quantity.value() + additionalQuantity.value());
        
        // 새로운 평균 단가
        BigDecimal newAveragePrice = existingValue.add(additionalValue)
                .divide(BigDecimal.valueOf(newQuantity.value()), 2, RoundingMode.HALF_UP);
        
        return new Position(symbol, newQuantity, Money.ofKrw(newAveragePrice));
    }
    
    /**
     * 포지션에서 일부 수량 제거
     */
    public Position reduceQuantity(Quantity reduceQuantity) {
        if (reduceQuantity.value() <= 0) {
            throw new IllegalArgumentException("Reduce quantity must be positive");
        }
        if (reduceQuantity.value() > quantity.value()) {
            throw new IllegalArgumentException("Cannot reduce more than current quantity");
        }
        
        Quantity newQuantity = Quantity.of(quantity.value() - reduceQuantity.value());
        
        // 평균 단가는 유지
        return new Position(symbol, newQuantity, averagePrice);
    }
    
    /**
     * 현재 시장 가격 기준 평가 금액 계산
     */
    public Money calculateMarketValue(Money currentPrice) {
        BigDecimal marketValue = currentPrice.amount()
                .multiply(BigDecimal.valueOf(quantity.value()));
        return Money.ofKrw(marketValue);
    }
    
    /**
     * 손익 계산 (현재 가격 - 평균 단가) * 수량
     */
    public Money calculateProfitLoss(Money currentPrice) {
        BigDecimal profitLoss = currentPrice.amount()
                .subtract(averagePrice.amount())
                .multiply(BigDecimal.valueOf(quantity.value()));
        return Money.ofKrw(profitLoss);
    }
    
    /**
     * 포지션이 비어있는지 확인
     */
    public boolean isEmpty() {
        return quantity.value() == 0;
    }
}