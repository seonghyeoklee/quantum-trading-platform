package com.quantum.api.kiwoom.dto.sector.chart;

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
 * 업종일봉조회응답 (ka20006) - 업종 일봉 차트 데이터 응답
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = false)
public class SectorDailyChartResponse extends BaseChartResponse {
    
    /**
     * 업종 일봉 차트 데이터 목록
     */
    @JsonProperty("output2")
    private List<SectorDailyCandleData> candleDataList;
    
    /**
     * 업종 일봉 캔들 데이터
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SectorDailyCandleData {
        
        /**
         * 일자 (YYYYMMDD)
         */
        @JsonProperty("stck_bsop_date")
        private String date;
        
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
        
        /**
         * 업종지수 전일대비부호
         * 1: 상한, 2: 상승, 3: 보합, 4: 하한, 5: 하락
         */
        @JsonProperty("bstp_nmix_prdy_vrss_sign")
        private String changeSign;
        
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
         * 캔들 실체 크기 (종가 - 시가)
         */
        public BigDecimal getCandleBodySize() {
            return getCloseIndex().subtract(getOpenIndex());
        }
        
        /**
         * 캔들 상단 그림자 크기 (고가 - max(시가, 종가))
         */
        public BigDecimal getUpperShadowSize() {
            BigDecimal maxOpenClose = getOpenIndex().max(getCloseIndex());
            return getHighIndex().subtract(maxOpenClose);
        }
        
        /**
         * 캔들 하단 그림자 크기 (min(시가, 종가) - 저가)
         */
        public BigDecimal getLowerShadowSize() {
            BigDecimal minOpenClose = getOpenIndex().min(getCloseIndex());
            return minOpenClose.subtract(getLowIndex());
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
            BigDecimal close = getCloseIndex();
            if (close.compareTo(BigDecimal.ZERO) == 0) {
                return BigDecimal.ZERO;
            }
            return range.divide(close, 4, BigDecimal.ROUND_HALF_UP).multiply(BigDecimal.valueOf(100));
        }
    }
    
    /**
     * 전체 캔들 데이터 개수
     */
    public int getCandleCount() {
        return candleDataList != null ? candleDataList.size() : 0;
    }
    
    /**
     * 최신 캔들 데이터 조회 (가장 최근 거래일)
     */
    public SectorDailyCandleData getLatestCandle() {
        if (candleDataList == null || candleDataList.isEmpty()) {
            return null;
        }
        return candleDataList.get(0); // 최신 데이터가 첫 번째
    }
    
    /**
     * 가장 오래된 캔들 데이터 조회
     */
    public SectorDailyCandleData getOldestCandle() {
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
                .map(SectorDailyCandleData::getHighIndex)
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
                .map(SectorDailyCandleData::getLowIndex)
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
    
    /**
     * 기간 내 평균 거래량
     */
    public BigDecimal getAverageVolume() {
        if (candleDataList == null || candleDataList.isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        long totalVolume = getTotalVolume();
        return BigDecimal.valueOf(totalVolume).divide(BigDecimal.valueOf(candleDataList.size()), 2, BigDecimal.ROUND_HALF_UP);
    }
    
    /**
     * 상승일/하락일/보합일 개수 통계
     */
    public TrendStatistics getTrendStatistics() {
        if (candleDataList == null || candleDataList.isEmpty()) {
            return new TrendStatistics(0, 0, 0);
        }
        
        int upDays = 0, downDays = 0, flatDays = 0;
        
        for (SectorDailyCandleData candle : candleDataList) {
            BigDecimal change = candle.getChangeAmount();
            if (change.compareTo(BigDecimal.ZERO) > 0) {
                upDays++;
            } else if (change.compareTo(BigDecimal.ZERO) < 0) {
                downDays++;
            } else {
                flatDays++;
            }
        }
        
        return new TrendStatistics(upDays, downDays, flatDays);
    }
    
    /**
     * 추세 통계 데이터
     */
    @Data
    @AllArgsConstructor
    public static class TrendStatistics {
        private int upDays;      // 상승일
        private int downDays;    // 하락일
        private int flatDays;    // 보합일
        
        public int getTotalDays() {
            return upDays + downDays + flatDays;
        }
        
        public BigDecimal getUpRatio() {
            int total = getTotalDays();
            if (total == 0) return BigDecimal.ZERO;
            return BigDecimal.valueOf(upDays).divide(BigDecimal.valueOf(total), 4, BigDecimal.ROUND_HALF_UP).multiply(BigDecimal.valueOf(100));
        }
        
        public BigDecimal getDownRatio() {
            int total = getTotalDays();
            if (total == 0) return BigDecimal.ZERO;
            return BigDecimal.valueOf(downDays).divide(BigDecimal.valueOf(total), 4, BigDecimal.ROUND_HALF_UP).multiply(BigDecimal.valueOf(100));
        }
    }
}