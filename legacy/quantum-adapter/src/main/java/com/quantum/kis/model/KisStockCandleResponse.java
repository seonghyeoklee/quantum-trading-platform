package com.quantum.kis.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * KIS API 주식 차트 조회 응답
 *
 * @param returnCode
 * @param messageCode
 * @param message
 * @param candleData
 * @param stockInfo
 */
public record KisStockCandleResponse(
        @JsonProperty("rt_cd") String returnCode,
        @JsonProperty("msg_cd") String messageCode,
        @JsonProperty("msg1") String message,
        @JsonProperty("output1") List<KisCandleData> candleData,
        @JsonProperty("output2") KisStockInfo stockInfo) {

    public boolean isSuccess() {
        return "0".equals(returnCode);
    }

    /**
     * KIS API 캔들 데이터
     *
     * @param businessDate
     * @param closePrice
     * @param openPrice
     * @param highPrice
     * @param lowPrice
     * @param accumulatedVolume
     * @param accumulatedAmount
     * @param fluctuationCode
     * @param fluctuationRate
     * @param modifiedYn
     */
    public record KisCandleData(
            @JsonProperty("stck_bsop_date") String businessDate, // 영업일자
            @JsonProperty("stck_clpr") String closePrice, // 종가
            @JsonProperty("stck_oprc") String openPrice, // 시가
            @JsonProperty("stck_hgpr") String highPrice, // 최고가
            @JsonProperty("stck_lwpr") String lowPrice, // 최저가
            @JsonProperty("acml_vol") String accumulatedVolume, // 누적거래량
            @JsonProperty("acml_tr_pbmn") String accumulatedAmount, // 누적거래대금
            @JsonProperty("flng_cls_code") String fluctuationCode, // 등락구분코드
            @JsonProperty("prtt_rate") String fluctuationRate, // 등락율
            @JsonProperty("mod_yn") String modifiedYn // 수정주가반영여부
            ) {}

    /**
     * KIS API 주식 기본 정보
     *
     * @param priorDayComparison
     * @param comparisonSign
     * @param priorDayRate
     * @param shortCode
     * @param productType
     */
    public record KisStockInfo(
            @JsonProperty("prdy_vrss") String priorDayComparison, // 전일대비
            @JsonProperty("prdy_vrss_sign") String comparisonSign, // 전일대비부호
            @JsonProperty("prdy_ctrt") String priorDayRate, // 전일대비율
            @JsonProperty("stck_shrn_iscd") String shortCode, // 주식단축종목코드
            @JsonProperty("stck_prdt_type_nm") String productType // 주식상품유형명
            ) {}
}
