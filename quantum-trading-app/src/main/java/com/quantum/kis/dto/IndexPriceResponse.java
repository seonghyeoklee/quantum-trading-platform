package com.quantum.kis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * KIS API 국내업종 현재지수 조회 응답 DTO
 * API: /uapi/domestic-stock/v1/quotations/inquire-index-price
 * TR_ID: FHPUP02100000
 */
public record IndexPriceResponse(
        @JsonProperty("rt_cd") String rtCd,           // 응답 코드
        @JsonProperty("msg_cd") String msgCd,         // 메시지 코드
        @JsonProperty("msg1") String msg1,            // 메시지
        @JsonProperty("output") Output output         // 출력 데이터
) {
    /**
     * 지수 정보
     */
    public record Output(
            @JsonProperty("bstp_nmix_prpr") String currentPrice,       // 업종 지수 현재가
            @JsonProperty("bstp_nmix_prdy_vrss") String priceChange,   // 업종 지수 전일 대비
            @JsonProperty("prdy_vrss_sign") String changeSign,         // 전일 대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
            @JsonProperty("bstp_nmix_prdy_ctrt") String changeRate,    // 업종 지수 전일 대비율
            @JsonProperty("acml_vol") String accumulatedVolume,        // 누적 거래량
            @JsonProperty("acml_tr_pbmn") String accumulatedAmount,    // 누적 거래 대금
            @JsonProperty("bstp_nmix_oprc") String openPrice,          // 업종 지수 시가
            @JsonProperty("bstp_nmix_hgpr") String highPrice,          // 업종 지수 최고가
            @JsonProperty("bstp_nmix_lwpr") String lowPrice            // 업종 지수 최저가
    ) {
        /**
         * 상승/하락 여부 판단
         * @return true if 상승, false if 하락 or 보합
         */
        public boolean isPositive() {
            return "1".equals(changeSign) || "2".equals(changeSign);
        }

        /**
         * 보합 여부 판단
         * @return true if 보합
         */
        public boolean isUnchanged() {
            return "3".equals(changeSign);
        }
    }

    /**
     * API 호출 성공 여부
     * @return true if 성공
     */
    public boolean isSuccess() {
        return "0".equals(rtCd);
    }
}
