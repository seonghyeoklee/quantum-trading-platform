package com.quantum.backtest.domain;

import java.util.Objects;
import java.util.UUID;

/**
 * 백테스팅 식별자 Value Object
 */
public record BacktestId(String value) {

    public BacktestId {
        Objects.requireNonNull(value, "BacktestId value cannot be null");
        if (value.isBlank()) {
            throw new IllegalArgumentException("BacktestId value cannot be blank");
        }
    }

    /**
     * 새로운 백테스팅 ID를 생성한다.
     */
    public static BacktestId generate() {
        return new BacktestId(UUID.randomUUID().toString());
    }

    /**
     * 문자열로부터 백테스팅 ID를 생성한다.
     */
    public static BacktestId from(String value) {
        return new BacktestId(value);
    }

    @Override
    public String toString() {
        return value;
    }
}