package com.quantum.kis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;
import java.util.List;

/**
 * KIS API 재무 데이터 조회 응답
 * 기업개요, 재무정보 등을 포함
 */
public record FinancialDataResponse(
        @JsonProperty("rt_cd") String rtCd,
        @JsonProperty("msg_cd") String msgCd,
        @JsonProperty("msg1") String msg1,
        @JsonProperty("output") FinancialData output
) {

    /**
     * 재무 데이터 세부 정보
     */
    public record FinancialData(
            @JsonProperty("hts_kor_isnm") String companyName,            // 한글 종목명
            @JsonProperty("sale_account") String currentRevenue,         // 당기 매출액
            @JsonProperty("sale_account_before") String previousRevenue, // 전기 매출액
            @JsonProperty("op_profit") String currentOperatingProfit,    // 당기 영업이익
            @JsonProperty("op_profit_before") String previousOperatingProfit, // 전기 영업이익
            @JsonProperty("total_debt") String totalDebt,                // 총부채
            @JsonProperty("total_stkprc") String totalEquity,            // 자기자본
            @JsonProperty("retained_earn") String retainedEarnings,      // 이익잉여금
            @JsonProperty("capital_stock") String capitalStock,          // 자본금
            @JsonProperty("settle_month") String currentPeriod,          // 당기 결산월
            @JsonProperty("settle_month_before") String previousPeriod   // 전기 결산월
    ) {

        /**
         * 매출액을 BigDecimal로 변환
         */
        public BigDecimal getCurrentRevenueBigDecimal() {
            return parseStringToBigDecimal(currentRevenue);
        }

        public BigDecimal getPreviousRevenueBigDecimal() {
            return parseStringToBigDecimal(previousRevenue);
        }

        /**
         * 영업이익을 BigDecimal로 변환
         */
        public BigDecimal getCurrentOperatingProfitBigDecimal() {
            return parseStringToBigDecimal(currentOperatingProfit);
        }

        public BigDecimal getPreviousOperatingProfitBigDecimal() {
            return parseStringToBigDecimal(previousOperatingProfit);
        }

        /**
         * 부채/자본 관련 데이터를 BigDecimal로 변환
         */
        public BigDecimal getTotalDebtBigDecimal() {
            return parseStringToBigDecimal(totalDebt);
        }

        public BigDecimal getTotalEquityBigDecimal() {
            return parseStringToBigDecimal(totalEquity);
        }

        public BigDecimal getRetainedEarningsBigDecimal() {
            return parseStringToBigDecimal(retainedEarnings);
        }

        public BigDecimal getCapitalStockBigDecimal() {
            return parseStringToBigDecimal(capitalStock);
        }

        /**
         * 문자열을 BigDecimal로 안전하게 변환
         * @param value 변환할 문자열 (KIS API는 숫자를 문자열로 반환)
         * @return BigDecimal 값, 변환 실패 시 null
         */
        private BigDecimal parseStringToBigDecimal(String value) {
            if (value == null || value.trim().isEmpty() || value.equals("0") || value.equals("-")) {
                return null;
            }

            try {
                // KIS API에서 콤마 등이 포함될 수 있으므로 제거
                String cleanValue = value.replaceAll("[,\\s]", "");
                return new BigDecimal(cleanValue);
            } catch (NumberFormatException e) {
                return null;
            }
        }

        /**
         * 유효한 재무 데이터인지 확인
         */
        public boolean hasValidFinancialData() {
            return companyName != null && !companyName.trim().isEmpty() &&
                   (getCurrentRevenueBigDecimal() != null || getPreviousRevenueBigDecimal() != null);
        }
    }
}