package com.quantum.kis.domain.token;

/**
 * 토큰 상태 열거형
 */
public enum TokenStatus {
    /**
     * 활성 상태 - 사용 가능한 토큰
     */
    ACTIVE("활성"),

    /**
     * 만료됨 - 유효 기간이 지난 토큰
     */
    EXPIRED("만료됨"),

    /**
     * 무효함 - 발급 실패하거나 사용할 수 없는 토큰
     */
    INVALID("무효함");

    private final String description;

    TokenStatus(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}