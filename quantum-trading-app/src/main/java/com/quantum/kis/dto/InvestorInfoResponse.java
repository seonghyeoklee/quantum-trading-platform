package com.quantum.kis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;
import java.util.List;

/**
 * KIS API 투자자별 매매동향 조회 응답
 * 기관투자자, 외국인 투자자의 매매 동향 정보
 */
public record InvestorInfoResponse(
        @JsonProperty("rt_cd") String rtCd,
        @JsonProperty("msg_cd") String msgCd,
        @JsonProperty("msg1") String msg1,
        @JsonProperty("output") List<InvestorInfo> output
) {

    /**
     * 투자자별 매매 정보
     */
    public record InvestorInfo(
            @JsonProperty("stck_bsop_date") String stockBusinessDate,      // 주식영업일자
            @JsonProperty("stck_clpr") String stockClosePrice,             // 주식종가
            @JsonProperty("prdy_vrss") String dayBeforeChange,              // 전일대비
            @JsonProperty("prdy_vrss_sign") String dayBeforeChangeSign,     // 전일대비부호
            @JsonProperty("prdy_ctrt") String dayBeforeRate,                // 전일대비율
            @JsonProperty("acml_vol") String accumulatedVolume,             // 누적거래량
            @JsonProperty("acml_tr_pbmn") String accumulatedTradingAmount,   // 누적거래대금
            @JsonProperty("seln_cntg_qty") String sellContingentQuantity,   // 매도수량
            @JsonProperty("shnu_cntg_qty") String buyContingentQuantity,    // 매수수량
            @JsonProperty("ntby_cntg_qty") String netBuyQuantity,           // 순매수수량
            @JsonProperty("seln_cntg_smtn") String sellContingentAmount,    // 매도금액
            @JsonProperty("shnu_cntg_smtn") String buyContingentAmount,     // 매수금액
            @JsonProperty("ntby_cntg_smtn") String netBuyAmount             // 순매수금액
    ) {

        /**
         * 순매수수량을 BigDecimal로 변환
         */
        public BigDecimal getNetBuyQuantityBigDecimal() {
            return parseStringToBigDecimal(netBuyQuantity);
        }

        /**
         * 순매수금액을 BigDecimal로 변환
         */
        public BigDecimal getNetBuyAmountBigDecimal() {
            return parseStringToBigDecimal(netBuyAmount);
        }

        /**
         * 매수수량을 BigDecimal로 변환
         */
        public BigDecimal getBuyQuantityBigDecimal() {
            return parseStringToBigDecimal(buyContingentQuantity);
        }

        /**
         * 매도수량을 BigDecimal로 변환
         */
        public BigDecimal getSellQuantityBigDecimal() {
            return parseStringToBigDecimal(sellContingentQuantity);
        }

        /**
         * 문자열을 BigDecimal로 안전하게 변환
         */
        private BigDecimal parseStringToBigDecimal(String value) {
            if (value == null || value.trim().isEmpty() || value.equals("0") || value.equals("-")) {
                return BigDecimal.ZERO;
            }

            try {
                String cleanValue = value.replaceAll("[,\\s]", "");
                return new BigDecimal(cleanValue);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }

        /**
         * 유효한 투자자 정보인지 확인
         */
        public boolean hasValidData() {
            return stockBusinessDate != null && !stockBusinessDate.trim().isEmpty() &&
                   netBuyQuantity != null && !netBuyQuantity.trim().isEmpty();
        }
    }
}