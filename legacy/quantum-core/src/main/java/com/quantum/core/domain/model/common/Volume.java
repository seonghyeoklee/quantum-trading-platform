package com.quantum.core.domain.model.common;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.Objects;

/**
 * 거래량 Value Object
 * 주식 거래량 관련 비즈니스 로직과 검증을 캡슐화
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Embeddable
public class Volume {

    @Column(name = "quantity")
    private Long quantity;

    private Volume(Long quantity) {
        validateQuantity(quantity);
        this.quantity = quantity;
    }

    public static Volume of(Long quantity) {
        return new Volume(quantity);
    }

    public static Volume zero() {
        return new Volume(0L);
    }

    private void validateQuantity(Long quantity) {
        if (quantity == null) {
            throw new IllegalArgumentException("거래량은 필수입니다");
        }
        if (quantity < 0) {
            throw new IllegalArgumentException("거래량은 0 이상이어야 합니다");
        }
    }

    public Volume add(Volume other) {
        return new Volume(this.quantity + other.quantity);
    }

    public Volume subtract(Volume other) {
        long result = this.quantity - other.quantity;
        if (result < 0) {
            throw new IllegalArgumentException("거래량은 음수가 될 수 없습니다");
        }
        return new Volume(result);
    }

    public boolean isZero() {
        return quantity == 0;
    }

    public boolean isPositive() {
        return quantity > 0;
    }

    public boolean isGreaterThan(Volume other) {
        return quantity > other.quantity;
    }

    public boolean isLessThan(Volume other) {
        return quantity < other.quantity;
    }

    public boolean isHighVolume(Volume averageVolume) {
        return quantity > averageVolume.quantity * 2; // 평균 거래량의 2배 이상
    }

    public boolean isLowVolume(Volume averageVolume) {
        return quantity < averageVolume.quantity / 2; // 평균 거래량의 50% 미만
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Volume volume = (Volume) o;
        return Objects.equals(quantity, volume.quantity);
    }

    @Override
    public int hashCode() {
        return Objects.hash(quantity);
    }

    @Override
    public String toString() {
        return String.format("%,d주", quantity);
    }
}