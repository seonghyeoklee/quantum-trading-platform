package com.quantum.api.application.port.out;

import com.quantum.kis.model.KisCurrentPriceResponse;

/** KIS 주식 가격 데이터 저장 전용 포트 (Command) CQRS 패턴 적용 - 조회와 저장 포트 분리 */
public interface KisStockPriceCommandPort {

    /**
     * KIS 원본 데이터 저장
     *
     * @param symbol 종목코드
     * @param response KIS API 응답
     */
    void saveKisData(String symbol, KisCurrentPriceResponse response);
}
