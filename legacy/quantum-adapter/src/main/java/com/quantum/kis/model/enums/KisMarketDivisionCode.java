package com.quantum.kis.model.enums;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/** KIS API 조건 시장 분류 코드 */
@Getter
@RequiredArgsConstructor
public enum KisMarketDivisionCode {
    KRX("J", "KRX 한국거래소"),
    NXT("NX", "NXT 넥스트 마켓"),
    UNIFIED("UN", "통합 시장");

    private final String code;
    private final String description;

    /** 기본값: KRX (한국거래소) */
    public static KisMarketDivisionCode getDefault() {
        return KRX;
    }
}
