package com.quantum.kis.model;

import com.quantum.kis.model.enums.KisMarketDivisionCode;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/** KIS API 주식 현재가 조회 쿼리 파라미터 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class KisCurrentPriceQueryParam {

    private String fidCondMrktDivCode; // 조건 시장 분류 코드
    private String fidInputIscd; // 입력 종목코드

    /** 국내 주식 현재가 조회용 파라미터 생성 (KIS API 공식 명세 기준) */
    public static KisCurrentPriceQueryParam forDomesticStock(String stockCode) {
        return KisCurrentPriceQueryParam.builder()
                .fidCondMrktDivCode(KisMarketDivisionCode.KRX.getCode()) // 기본: KRX 한국거래소
                .fidInputIscd(validateStockCode(stockCode)) // 종목코드 (예: 005930, ETN은 Q 접두사)
                .build();
    }

    /** 시장별 주식 현재가 조회용 파라미터 생성 */
    public static KisCurrentPriceQueryParam forStock(
            String stockCode, KisMarketDivisionCode marketCode) {
        return KisCurrentPriceQueryParam.builder()
                .fidCondMrktDivCode(marketCode.getCode())
                .fidInputIscd(validateStockCode(stockCode))
                .build();
    }

    /** 종목코드 검증 및 ETN 처리 */
    private static String validateStockCode(String stockCode) {
        if (stockCode == null || stockCode.trim().isEmpty()) {
            throw new IllegalArgumentException("종목코드는 필수입니다");
        }

        String trimmed = stockCode.trim();

        // ETN 종목코드는 6자리 앞에 Q 접두사 필요
        if (trimmed.length() == 6 && !trimmed.startsWith("Q")) {
            // ETN 여부는 별도 로직으로 판단 필요 (현재는 일반 주식으로 처리)
            return trimmed;
        }

        return trimmed;
    }
}
