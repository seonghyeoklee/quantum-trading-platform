package com.quantum.core.domain.model.common;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * 거래소 코드 열거형
 * 주식 거래소 종류를 타입 안전하게 관리
 */
@Getter
@RequiredArgsConstructor
public enum ExchangeCode {

    KOSPI("KOSPI", "한국종합주가지수", "KR"),
    KOSDAQ("KOSDAQ", "코스닥", "KR"),
    KRX("KRX", "한국거래소", "KR"),
    NASDAQ("NASDAQ", "나스닥", "US"),
    NYSE("NYSE", "뉴욕증권거래소", "US");

    private final String code;
    private final String koreanName;
    private final String countryCode;

    public static ExchangeCode fromCode(String code) {
        if (code == null || code.trim().isEmpty()) {
            return KOSPI; // 기본값
        }
        
        for (ExchangeCode exchange : values()) {
            if (exchange.code.equalsIgnoreCase(code.trim())) {
                return exchange;
            }
        }
        
        throw new IllegalArgumentException("지원하지 않는 거래소 코드: " + code);
    }

    public boolean isKorean() {
        return "KR".equals(countryCode);
    }

    public boolean isUs() {
        return "US".equals(countryCode);
    }
}