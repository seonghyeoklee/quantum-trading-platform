package com.quantum.kis.domain;

/**
 * KIS API 환경 구분
 * - PROD: 실전투자 환경
 * - VPS: 모의투자 환경
 */
public enum KisEnvironment {
    PROD("실전투자"),
    VPS("모의투자");

    private final String description;

    KisEnvironment(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}