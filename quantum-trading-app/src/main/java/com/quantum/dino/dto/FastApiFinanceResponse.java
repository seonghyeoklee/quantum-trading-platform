package com.quantum.dino.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;

/**
 * quantum-adapter-kis FastAPI 재무 정보 응답
 * /dino-test/finance/{stock_code} 엔드포인트 응답 매핑
 */
public record FastApiFinanceResponse(
        @JsonProperty("stock_code") String stockCode,
        @JsonProperty("stock_name") String stockName,
        @JsonProperty("total_score") Integer totalScore,
        @JsonProperty("score_details") ScoreDetails scoreDetails,
        @JsonProperty("raw_data") RawData rawData
) {

    /**
     * 점수 상세 정보
     */
    public record ScoreDetails(
            @JsonProperty("revenue_growth_score") Integer revenueGrowthScore,
            @JsonProperty("operating_profit_score") Integer operatingProfitScore,
            @JsonProperty("operating_margin_score") Integer operatingMarginScore,
            @JsonProperty("retained_earnings_ratio_score") Integer retentionRateScore,
            @JsonProperty("debt_ratio_score") Integer debtRatioScore,
            @JsonProperty("revenue_growth_rate") Double revenueGrowthRate,
            @JsonProperty("operating_profit_transition") String operatingProfitTransition,
            @JsonProperty("operating_margin_rate") Double operatingMarginRate,
            @JsonProperty("retained_earnings_ratio") Double retentionRate,
            @JsonProperty("debt_ratio") Double debtRatio
    ) {
    }

    /**
     * 원시 재무 데이터
     */
    public record RawData(
            @JsonProperty("기준기간") String basePeriod,
            @JsonProperty("당년매출액") String currentRevenue,
            @JsonProperty("전년매출액") String previousRevenue,
            @JsonProperty("당년영업이익") String currentOperatingProfit,
            @JsonProperty("전년영업이익") String previousOperatingProfit,
            @JsonProperty("총부채") String totalDebt,
            @JsonProperty("자기자본") String totalEquity,
            @JsonProperty("이익잉여금") String retainedEarnings,
            @JsonProperty("자본금") String capitalStock
    ) {

        /**
         * 문자열을 BigDecimal로 안전하게 변환
         * @param value 변환할 문자열 (예: "1,537,068억원")
         * @return BigDecimal 값, 변환 실패 시 null
         */
        private BigDecimal parseStringToBigDecimal(String value) {
            if (value == null || value.trim().isEmpty() || value.equals("null")) {
                return null;
            }

            try {
                // "1,537,068억원" → "153706800000000" 변환
                String cleanValue = value.replaceAll("[,\\s억원만원천원]", "");

                // "억원" 단위 처리 (x10^8)
                if (value.contains("억원")) {
                    return new BigDecimal(cleanValue).multiply(BigDecimal.valueOf(100000000L));
                }
                // "만원" 단위 처리 (x10^4)
                else if (value.contains("만원")) {
                    return new BigDecimal(cleanValue).multiply(BigDecimal.valueOf(10000L));
                }
                // "천원" 단위 처리 (x10^3)
                else if (value.contains("천원")) {
                    return new BigDecimal(cleanValue).multiply(BigDecimal.valueOf(1000L));
                }
                // 단위 없는 경우
                else {
                    return new BigDecimal(cleanValue);
                }
            } catch (NumberFormatException e) {
                return null;
            }
        }

        public BigDecimal getCurrentRevenueBigDecimal() {
            return parseStringToBigDecimal(currentRevenue);
        }

        public BigDecimal getPreviousRevenueBigDecimal() {
            return parseStringToBigDecimal(previousRevenue);
        }

        public BigDecimal getCurrentOperatingProfitBigDecimal() {
            return parseStringToBigDecimal(currentOperatingProfit);
        }

        public BigDecimal getPreviousOperatingProfitBigDecimal() {
            return parseStringToBigDecimal(previousOperatingProfit);
        }

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
         * 유효한 재무 데이터인지 확인
         */
        public boolean hasValidFinancialData() {
            return currentRevenue != null && !currentRevenue.trim().isEmpty() &&
                   !currentRevenue.equals("null") &&
                   (getCurrentRevenueBigDecimal() != null || getPreviousRevenueBigDecimal() != null);
        }
    }
}