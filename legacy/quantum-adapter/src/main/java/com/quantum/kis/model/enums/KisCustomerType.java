package com.quantum.kis.model.enums;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/** KIS API 고객 타입 */
@Getter
@RequiredArgsConstructor
public enum KisCustomerType {
    PERSONAL("P", "개인"),
    CORPORATE("B", "법인");

    private final String code;
    private final String description;

    /** 기본값: 개인 */
    public static KisCustomerType getDefault() {
        return PERSONAL;
    }
}
