package com.quantum.kis.model.enums;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/** KIS API 거래 ID (TR_ID) */
@Getter
@RequiredArgsConstructor
public enum KisTransactionId {
    CURRENT_PRICE("FHKST01010100", "주식현재가 조회"),
    DAILY_CANDLE("FHKST03010100", "국내주식 일봉차트조회"),
    MINUTE_CANDLE("FHKST03010200", "국내주식 분봉차트조회"),
    ACCOUNT_BALANCE("TTTC8434R", "주식잔고조회"),
    DOMESTIC_STOCK_MULTI_PRICE_REAL("FHKST11300006", "관심종목(멀티종목) 시세조회 - 실전투자"),
    DOMESTIC_STOCK_MULTI_PRICE_SANDBOX("FHKST11300012", "관심종목(멀티종목) 시세조회 - 모의투자");

    private final String code;
    private final String description;

    /** TR ID 코드 반환 */
    public String getId() {
        return this.code;
    }
}
