package com.quantum.core.domain.model.common;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

import java.util.Arrays;
import java.util.List;

/**
 * 주식 지역 구분 열거형
 * 국내주식과 해외주식을 구분하여 차트 분석 전략을 다르게 적용
 */
@Getter
@RequiredArgsConstructor
public enum StockRegion {

    DOMESTIC("국내", "KR", List.of(ExchangeCode.KOSPI, ExchangeCode.KOSDAQ, ExchangeCode.KRX)),
    OVERSEAS("해외", "GLOBAL", List.of(ExchangeCode.NASDAQ, ExchangeCode.NYSE));

    private final String koreanName;
    private final String regionCode;
    private final List<ExchangeCode> supportedExchanges;

    /**
     * 거래소 코드로부터 지역 구분
     */
    public static StockRegion fromExchange(ExchangeCode exchange) {
        return Arrays.stream(values())
                .filter(region -> region.supportedExchanges.contains(exchange))
                .findFirst()
                .orElse(DOMESTIC); // 기본값: 국내
    }

    /**
     * 국내 주식 여부
     */
    public boolean isDomestic() {
        return this == DOMESTIC;
    }

    /**
     * 해외 주식 여부
     */
    public boolean isOverseas() {
        return this == OVERSEAS;
    }

    /**
     * 해당 지역에서 지원하는 거래소인지 확인
     */
    public boolean supports(ExchangeCode exchange) {
        return supportedExchanges.contains(exchange);
    }
}