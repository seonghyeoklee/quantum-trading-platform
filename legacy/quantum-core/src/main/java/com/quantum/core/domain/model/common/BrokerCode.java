package com.quantum.core.domain.model.common;

import lombok.Getter;

/** 증권사 코드 Enum */
@Getter
public enum BrokerCode {
    KIS("KIS", "한국투자증권"),
    KIWOOM("KIWOOM", "키움증권"),
    EBEST("EBEST", "이베스트투자증권");

    private final String code;
    private final String koreanName;

    BrokerCode(String code, String koreanName) {
        this.code = code;
        this.koreanName = koreanName;
    }

    /** 문자열 코드로부터 BrokerCode 생성 */
    public static BrokerCode fromCode(String code) {
        if (code == null || code.trim().isEmpty()) {
            throw new IllegalArgumentException("증권사 코드는 필수입니다");
        }

        String trimmed = code.trim().toLowerCase();
        for (BrokerCode broker : values()) {
            if (broker.code.equals(trimmed)) {
                return broker;
            }
        }

        throw new IllegalArgumentException("지원하지 않는 증권사 코드: " + code);
    }

    /** KIS 증권사인지 확인 */
    public boolean isKis() {
        return this == KIS;
    }

    /** 키움증권인지 확인 */
    public boolean isKiwoom() {
        return this == KIWOOM;
    }

    @Override
    public String toString() {
        return code;
    }
}
