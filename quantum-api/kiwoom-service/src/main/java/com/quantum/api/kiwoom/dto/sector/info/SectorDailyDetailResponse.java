package com.quantum.api.kiwoom.dto.sector.info;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.BaseChartResponse;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * 업종현재가일별응답 (ka20009) - 업종 일별 상세 현재가 데이터 응답
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = false)
public class SectorDailyDetailResponse extends BaseChartResponse {
    
    /**
     * 업종 일별 상세 데이터 목록
     */
    @JsonProperty("output2")
    private List<SectorDailyDetailData> dailyDetailList;
    
    /**
     * 업종 일별 상세 데이터
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SectorDailyDetailData {
        
        /**
         * 일자 (YYYYMMDD)
         */
        @JsonProperty("stck_bsop_date")
        private String date;
        
        /**
         * 업종명
         */
        @JsonProperty("bstp_kor_isnm")
        private String sectorName;
        
        /**
         * 업종코드
         */
        @JsonProperty("bstp_nmix_prpr")
        private String sectorCode;
        
        /**
         * 업종지수 (현재가)
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_prpr")
        private String currentIndexRaw;
        
        /**
         * 업종지수 전일대비
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_prdy_vrss")
        private String changeAmountRaw;
        
        /**
         * 업종지수 등락율
         */
        @JsonProperty("bstp_nmix_prdy_ctrt")
        private String changeRate;
        
        /**
         * 업종지수 전일대비부호
         * 1: 상한, 2: 상승, 3: 보합, 4: 하한, 5: 하락
         */
        @JsonProperty("bstp_nmix_prdy_vrss_sign")
        private String changeSign;
        
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
         * 업종지수 시가
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_oprc")
        private String openIndexRaw;
        
        /**
         * 업종지수 고가
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_hgpr")
        private String highIndexRaw;
        
        /**
         * 업종지수 저가
         * 실제값 = API응답값 / 100.0
         */
        @JsonProperty("bstp_nmix_lwpr")
        private String lowIndexRaw;
        
        /**
         * 상장종목수
         */
        @JsonProperty("lstg_stcn")
        private Integer listedStockCount;
        
        /**
         * 상승종목수
         */
        @JsonProperty("aspr_stcn")
        private Integer risingStockCount;
        
        /**
         * 하락종목수
         */
        @JsonProperty("down_stcn")
        private Integer fallingStockCount;
        
        /**
         * 보합종목수
         */
        @JsonProperty("bspr_stcn")
        private Integer unchangedStockCount;
        
        /**
         * 상한종목수
         */
        @JsonProperty("uplmt_stcn")
        private Integer upperLimitStockCount;
        
        /**
         * 하한종목수
         */
        @JsonProperty("lwlmt_stcn")
        private Integer lowerLimitStockCount;
        
        /**
         * 평균등락율
         */
        @JsonProperty("avrg_cnpr")
        private String averageChangeRate;
        
        // === 계산된 속성 (소수점 변환) ===
        
        /**
         * 현재 지수 (실제값)
         */
        public BigDecimal getCurrentIndex() {
            if (currentIndexRaw == null || currentIndexRaw.trim().isEmpty()) {
                return BigDecimal.ZERO;
            }
            try {
                return new BigDecimal(currentIndexRaw.trim()).divide(BigDecimal.valueOf(100), 2, BigDecimal.ROUND_HALF_UP);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }
        
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
         * 평균등락율 (%)
         */
        public BigDecimal getAverageChangeRatePercent() {
            if (averageChangeRate == null || averageChangeRate.trim().isEmpty()) {
                return BigDecimal.ZERO;
            }
            try {
                return new BigDecimal(averageChangeRate.trim());
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }
        
        /**
         * 일자 (YYYY-MM-DD)
         */
        public String getFormattedDate() {
            if (date == null || date.length() != 8) {
                return date;
            }
            
            try {
                return date.substring(0, 4) + "-" + 
                       date.substring(4, 6) + "-" + 
                       date.substring(6, 8);
            } catch (Exception e) {
                return date;
            }
        }
        
        /**
         * LocalDate 객체로 변환
         */
        public LocalDate getLocalDate() {
            if (date == null || date.length() != 8) {
                return null;
            }
            
            try {
                return LocalDate.parse(date, DateTimeFormatter.ofPattern("yyyyMMdd"));
            } catch (Exception e) {
                return null;
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
         * 상승/하락 여부 판단 (등락부호 기준)
         */
        public String getTrend() {
            if (changeSign == null) {
                BigDecimal change = getChangeAmount();
                if (change.compareTo(BigDecimal.ZERO) > 0) {
                    return "상승";
                } else if (change.compareTo(BigDecimal.ZERO) < 0) {
                    return "하락";
                } else {
                    return "보합";
                }
            }
            
            switch (changeSign) {
                case "1": return "상한";
                case "2": return "상승";
                case "3": return "보합";
                case "4": return "하한";
                case "5": return "하락";
                default: return "알수없음";
            }
        }
        
        /**
         * 등락부호 색상 코드
         */
        public String getTrendColor() {
            if (changeSign == null) {
                BigDecimal change = getChangeAmount();
                if (change.compareTo(BigDecimal.ZERO) > 0) {
                    return "red";
                } else if (change.compareTo(BigDecimal.ZERO) < 0) {
                    return "blue";
                } else {
                    return "black";
                }
            }
            
            switch (changeSign) {
                case "1": case "2": return "red";   // 상승/상한
                case "4": case "5": return "blue";  // 하락/하한
                case "3": return "black";           // 보합
                default: return "gray";
            }
        }
        
        /**
         * 종목 분포 통계
         */
        public StockDistribution getStockDistribution() {
            return StockDistribution.builder()
                    .totalStocks(listedStockCount != null ? listedStockCount : 0)
                    .risingStocks(risingStockCount != null ? risingStockCount : 0)
                    .fallingStocks(fallingStockCount != null ? fallingStockCount : 0)
                    .unchangedStocks(unchangedStockCount != null ? unchangedStockCount : 0)
                    .upperLimitStocks(upperLimitStockCount != null ? upperLimitStockCount : 0)
                    .lowerLimitStocks(lowerLimitStockCount != null ? lowerLimitStockCount : 0)
                    .build();
        }
        
        /**
         * 상승 종목 비율 (%)
         */
        public BigDecimal getRisingStockRatio() {
            if (listedStockCount == null || listedStockCount == 0 || risingStockCount == null) {
                return BigDecimal.ZERO;
            }
            return BigDecimal.valueOf(risingStockCount)
                    .divide(BigDecimal.valueOf(listedStockCount), 4, BigDecimal.ROUND_HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
        }
        
        /**
         * 하락 종목 비율 (%)
         */
        public BigDecimal getFallingStockRatio() {
            if (listedStockCount == null || listedStockCount == 0 || fallingStockCount == null) {
                return BigDecimal.ZERO;
            }
            return BigDecimal.valueOf(fallingStockCount)
                    .divide(BigDecimal.valueOf(listedStockCount), 4, BigDecimal.ROUND_HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
        }
        
        /**
         * 시장 강도 지수 (상승종목수 - 하락종목수)
         */
        public Integer getMarketStrength() {
            if (risingStockCount == null || fallingStockCount == null) {
                return 0;
            }
            return risingStockCount - fallingStockCount;
        }
        
        /**
         * 일일 변동성 (고가 - 저가)
         */
        public BigDecimal getDailyRange() {
            return getHighIndex().subtract(getLowIndex());
        }
        
        /**
         * 일일 변동성 비율 (%)
         */
        public BigDecimal getDailyRangePercent() {
            BigDecimal range = getDailyRange();
            BigDecimal current = getCurrentIndex();
            if (current.compareTo(BigDecimal.ZERO) == 0) {
                return BigDecimal.ZERO;
            }
            return range.divide(current, 4, BigDecimal.ROUND_HALF_UP).multiply(BigDecimal.valueOf(100));
        }
    }
    
    /**
     * 종목 분포 통계 클래스
     */
    @Data
    @Builder
    @AllArgsConstructor
    public static class StockDistribution {
        private Integer totalStocks;      // 전체 종목수
        private Integer risingStocks;     // 상승 종목수
        private Integer fallingStocks;    // 하락 종목수
        private Integer unchangedStocks;  // 보합 종목수
        private Integer upperLimitStocks; // 상한 종목수
        private Integer lowerLimitStocks; // 하한 종목수
        
        public BigDecimal getRisingRatio() {
            if (totalStocks == 0) return BigDecimal.ZERO;
            return BigDecimal.valueOf(risingStocks).divide(BigDecimal.valueOf(totalStocks), 4, BigDecimal.ROUND_HALF_UP).multiply(BigDecimal.valueOf(100));
        }
        
        public BigDecimal getFallingRatio() {
            if (totalStocks == 0) return BigDecimal.ZERO;
            return BigDecimal.valueOf(fallingStocks).divide(BigDecimal.valueOf(totalStocks), 4, BigDecimal.ROUND_HALF_UP).multiply(BigDecimal.valueOf(100));
        }
        
        public Integer getNetChange() {
            return risingStocks - fallingStocks;
        }
    }
    
    /**
     * 전체 일별 데이터 개수
     */
    public int getDataCount() {
        return dailyDetailList != null ? dailyDetailList.size() : 0;
    }
    
    /**
     * 최신 일별 데이터 조회
     */
    public SectorDailyDetailData getLatestData() {
        if (dailyDetailList == null || dailyDetailList.isEmpty()) {
            return null;
        }
        return dailyDetailList.get(0); // 최신 데이터가 첫 번째
    }
    
    /**
     * 가장 오래된 일별 데이터 조회
     */
    public SectorDailyDetailData getOldestData() {
        if (dailyDetailList == null || dailyDetailList.isEmpty()) {
            return null;
        }
        return dailyDetailList.get(dailyDetailList.size() - 1); // 오래된 데이터가 마지막
    }
    
    /**
     * 기간 내 최고지수 조회
     */
    public BigDecimal getPeriodHighIndex() {
        if (dailyDetailList == null || dailyDetailList.isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return dailyDetailList.stream()
                .map(SectorDailyDetailData::getHighIndex)
                .max(BigDecimal::compareTo)
                .orElse(BigDecimal.ZERO);
    }
    
    /**
     * 기간 내 최저지수 조회
     */
    public BigDecimal getPeriodLowIndex() {
        if (dailyDetailList == null || dailyDetailList.isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return dailyDetailList.stream()
                .map(SectorDailyDetailData::getLowIndex)
                .min(BigDecimal::compareTo)
                .orElse(BigDecimal.ZERO);
    }
    
    /**
     * 기간 내 총 거래량 합계
     */
    public Long getTotalVolume() {
        if (dailyDetailList == null || dailyDetailList.isEmpty()) {
            return 0L;
        }
        
        return dailyDetailList.stream()
                .mapToLong(data -> data.getVolume() != null ? data.getVolume() : 0L)
                .sum();
    }
    
    /**
     * 기간 내 평균 거래량
     */
    public BigDecimal getAverageVolume() {
        if (dailyDetailList == null || dailyDetailList.isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        long totalVolume = getTotalVolume();
        return BigDecimal.valueOf(totalVolume).divide(BigDecimal.valueOf(dailyDetailList.size()), 2, BigDecimal.ROUND_HALF_UP);
    }
}