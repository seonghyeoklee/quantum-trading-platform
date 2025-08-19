package com.quantum.api.application.port.out;

import com.quantum.kis.model.KisCurrentPriceResponse;

/** KIS 주식 가격 데이터 조회 전용 포트 (Query) CQRS 패턴 적용 - 조회와 저장 포트 분리 */
public interface KisStockPriceQueryPort {

    /**
     * 종목코드로 KIS 원본 응답 조회
     *
     * @param symbol 종목코드 (예: "005930")
     * @return KIS API 원본 응답
     */
    KisCurrentPriceResponse getCurrentPriceFromKis(String symbol);
}
