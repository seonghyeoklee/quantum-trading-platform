package com.quantum.api.kiwoom.dto.sector.chart;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.BaseChartResponse;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

/**
 * 업종분봉조회응답 (ka20005) - 업종 분봉 차트 데이터 응답
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = false)
public class SectorMinuteChartResponse extends BaseChartResponse {
    
    /**
     * 업종 분봉 차트 데이터 목록
     */
    @JsonProperty("output2")
    private List<SectorMinuteCandleData> candleDataList;
    
    /**
     * 업종 분봉 캔들 데이터
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SectorMinuteCandleData {
        
        /**
         * 일자 (YYYYMMDD)
         */
        @JsonProperty("stck_bsop_date")
        private String date;
        
        /**
         * 시간 (HHMMSS)
         */
        @JsonProperty("stck_cntg_hour")
        private String time;
        
        /**
         * 업종지수 (시가)
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_oprc")
        private String openIndexRaw;
        
        /**
         * 업종지수 (고가)
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_hgpr")
        private String highIndexRaw;
        
        /**
         * 업종지수 (저가)
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_lwpr")
        private String lowIndexRaw;
        
        /**
         * 업종지수 (종가)
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_prpr")
        private String closeIndexRaw;
        
        /**
         * 거래량
         */
        @JsonProperty("acml_vol")
        private Long volume;
        
        /**
         * 거래대금 (천원)
         */
        @JsonProperty("acml_tr_pbmn")
        private Long tradingValue;
        
        /**
         * 업종지수 등락율
         */
        @JsonProperty("bstp_nmix_prdy_ctrt")
        private String changeRate;
        
        /**
         * 업종지수 등락폭
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_prdy_vrss")
        private String changeAmountRaw;
        
        // === 계산된 속성 (소수점 변환) ===
        
        /**
         * 시가 지수 (실제값)
         */
        public BigDecimal getOpenIndex() {
            if (openIndexRaw == null || openIndexRaw.trim().isEmpty()) {
                return BigDecimal.ZERO;
            }
            try {
                return new BigDecimal(openIndexRaw.trim()).divide(BigDecimal.valueOf(100), 2, BigDecimal.ROUND_HALF_UP);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }
        
        /**
         * 고가 지수 (실제값)
         */
        public BigDecimal getHighIndex() {
            if (highIndexRaw == null || highIndexRaw.trim().isEmpty()) {
                return BigDecimal.ZERO;
            }
            try {
                return new BigDecimal(highIndexRaw.trim()).divide(BigDecimal.valueOf(100), 2, BigDecimal.ROUND_HALF_UP);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }
        
        /**
         * 저가 지수 (실제값)
         */
        public BigDecimal getLowIndex() {
            if (lowIndexRaw == null || lowIndexRaw.trim().isEmpty()) {
                return BigDecimal.ZERO;
            }
            try {
                return new BigDecimal(lowIndexRaw.trim()).divide(BigDecimal.valueOf(100), 2, BigDecimal.ROUND_HALF_UP);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }
        
        /**
         * 종가 지수 (실제값)
         */
        public BigDecimal getCloseIndex() {
            if (closeIndexRaw == null || closeIndexRaw.trim().isEmpty()) {
                return BigDecimal.ZERO;
            }
            try {
                return new BigDecimal(closeIndexRaw.trim()).divide(BigDecimal.valueOf(100), 2, BigDecimal.ROUND_HALF_UP);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }
        
        /**
         * 등락폭 (실제값)
         */
        public BigDecimal getChangeAmount() {
            if (changeAmountRaw == null || changeAmountRaw.trim().isEmpty()) {
                return BigDecimal.ZERO;
            }
            try {
                return new BigDecimal(changeAmountRaw.trim()).divide(BigDecimal.valueOf(100), 2, BigDecimal.ROUND_HALF_UP);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }
        
        /**
         * 등락율 (%)
         */
        public BigDecimal getChangeRatePercent() {
            if (changeRate == null || changeRate.trim().isEmpty()) {
                return BigDecimal.ZERO;
            }
            try {
                return new BigDecimal(changeRate.trim());
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }
        
        /**
         * 일시 (YYYY-MM-DD HH:mm:ss)
         */
        public String getFormattedDateTime() {
            if (date == null || time == null) {
                return "";
            }
            
            try {
                String formattedDate = date.substring(0, 4) + "-" + 
                                     date.substring(4, 6) + "-" + 
                                     date.substring(6, 8);
                String formattedTime = time.substring(0, 2) + ":" + 
                                     time.substring(2, 4) + ":" + 
                                     time.substring(4, 6);
                return formattedDate + " " + formattedTime;
            } catch (Exception e) {
                return date + " " + time;
            }
        }
        
        /**
         * 거래대금 (억원 단위)
         */
        public BigDecimal getTradingValueInEokWon() {
            if (tradingValue == null) {
                return BigDecimal.ZERO;
            }
            return BigDecimal.valueOf(tradingValue).divide(BigDecimal.valueOf(100_000), 2, BigDecimal.ROUND_HALF_UP);
        }
        
        /**
         * 상승/하락 여부 판단
         */
        public String getTrend() {
            BigDecimal change = getChangeAmount();
            if (change.compareTo(BigDecimal.ZERO) > 0) {
                return "상승";
            } else if (change.compareTo(BigDecimal.ZERO) < 0) {
                return "하락";
            } else {
                return "보합";
            }
        }
    }
    
    /**
     * 전체 캔들 데이터 개수
     */
    public int getCandleCount() {
        return candleDataList != null ? candleDataList.size() : 0;
    }
    
    /**
     * 최신 캔들 데이터 조회
     */
    public SectorMinuteCandleData getLatestCandle() {
        if (candleDataList == null || candleDataList.isEmpty()) {
            return null;
        }
        return candleDataList.get(0); // 최신 데이터가 첫 번째
    }
    
    /**
     * 가장 오래된 캔들 데이터 조회
     */
    public SectorMinuteCandleData getOldestCandle() {
        if (candleDataList == null || candleDataList.isEmpty()) {
            return null;
        }
        return candleDataList.get(candleDataList.size() - 1); // 오래된 데이터가 마지막
    }
    
    /**
     * 기간 내 최고가 조회
     */
    public BigDecimal getPeriodHighIndex() {
        if (candleDataList == null || candleDataList.isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return candleDataList.stream()
                .map(SectorMinuteCandleData::getHighIndex)
                .max(BigDecimal::compareTo)
                .orElse(BigDecimal.ZERO);
    }
    
    /**
     * 기간 내 최저가 조회
     */
    public BigDecimal getPeriodLowIndex() {
        if (candleDataList == null || candleDataList.isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return candleDataList.stream()
                .map(SectorMinuteCandleData::getLowIndex)
                .min(BigDecimal::compareTo)
                .orElse(BigDecimal.ZERO);
    }
    
    /**
     * 기간 내 총 거래량 합계
     */
    public Long getTotalVolume() {
        if (candleDataList == null || candleDataList.isEmpty()) {
            return 0L;
        }
        
        return candleDataList.stream()
                .mapToLong(candle -> candle.getVolume() != null ? candle.getVolume() : 0L)
                .sum();
    }
}