package com.quantum.api.kiwoom.dto.chart.sector;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.CandleData;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 업종틱차트 개별 데이터
 * 키움 API upjong_tic_chart_qry 배열의 각 요소
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "업종틱차트 개별 데이터")
public class SectorTickChartData {
    
    /**
     * 현재지수
     */
    @JsonProperty("cur_prc")
    @Schema(description = "현재지수", example = "2500.15")
    private String currentIndex;
    
    /**
     * 거래량
     */
    @JsonProperty("trde_qty")
    @Schema(description = "거래량", example = "1000000")
    private String tradeQuantity;
    
    /**
     * 거래대금
     */
    @JsonProperty("trde_prica")
    @Schema(description = "거래대금", example = "133600000000")
    private String tradeAmount;
    
    /**
     * 거래시간 (HHMMSS)
     */
    @JsonProperty("cntr_tm")
    @Schema(description = "거래시간", example = "153000")
    private String contractTime;
    
    /**
     * 수정주가구분
     */
    @JsonProperty("upd_stkpc_tp")
    @Schema(description = "수정주가구분")
    private String updateStockPriceType;
    
    /**
     * 수정비율
     */
    @JsonProperty("upd_rt")
    @Schema(description = "수정비율", example = "+0.83")
    private String updateRate;
    
    /**
     * 대업종구분
     */
    @JsonProperty("bic_inds_tp")
    @Schema(description = "대업종구분")
    private String bigIndustryType;
    
    /**
     * 소업종구분
     */
    @JsonProperty("sm_inds_tp")
    @Schema(description = "소업종구분")
    private String smallIndustryType;
    
    /**
     * 업종정보
     */
    @JsonProperty("upjong_infr")
    @Schema(description = "업종정보")
    private String sectorInfo;
    
    /**
     * 수정주가이벤트
     */
    @JsonProperty("upd_stkpc_event")
    @Schema(description = "수정주가이벤트")
    private String updateStockPriceEvent;
    
    /**
     * 전일지수
     */
    @JsonProperty("pred_close_pric")
    @Schema(description = "전일지수", example = "2495.20")
    private String previousCloseIndex;
    
    // ===== 유틸리티 메서드 =====
    
    /**
     * 공통 CandleData로 변환 (업종 틱은 지수가 OHLC)
     */
    public CandleData toCandleData() {
        return CandleData.builder()
                .currentPrice(currentIndex)
                .openPrice(currentIndex)       // 업종 틱은 시가 = 현재지수
                .highPrice(currentIndex)       // 업종 틱은 고가 = 현재지수
                .lowPrice(currentIndex)        // 업종 틱은 저가 = 현재지수
                .tradeQuantity(tradeQuantity)
                .tradeAmount(tradeAmount)
                .date(contractTime) // 업종 틱은 시간 정보 사용
                .updateStockPriceType(updateStockPriceType)
                .updateRate(updateRate)
                .previousClosePrice(previousCloseIndex)
                .build();
    }
    
    /**
     * 현재지수를 BigDecimal로 변환
     */
    public BigDecimal getCurrentIndexAsDecimal() {
        return parseIndex(currentIndex);
    }
    
    /**
     * 전일지수를 BigDecimal로 변환
     */
    public BigDecimal getPreviousCloseIndexAsDecimal() {
        return parseIndex(previousCloseIndex);
    }
    
    /**
     * 거래량을 Long으로 변환
     */
    public Long getTradeQuantityAsLong() {
        if (tradeQuantity == null || tradeQuantity.trim().isEmpty()) {
            return 0L;
        }
        try {
            return Long.parseLong(tradeQuantity.replace(",", ""));
        } catch (NumberFormatException e) {
            return 0L;
        }
    }
    
    /**
     * 거래대금을 BigDecimal로 변환
     */
    public BigDecimal getTradeAmountAsDecimal() {
        return parseIndex(tradeAmount);
    }
    
    /**
     * 거래시간을 LocalDateTime으로 변환 (오늘 날짜 기준)
     */
    public LocalDateTime getContractTimeAsLocalDateTime() {
        if (contractTime == null || contractTime.length() != 6) {
            return null;
        }
        try {
            String timeStr = String.format("%s:%s:%s", 
                    contractTime.substring(0, 2),
                    contractTime.substring(2, 4),
                    contractTime.substring(4, 6));
            return LocalDateTime.parse(
                    LocalDateTime.now().toLocalDate() + "T" + timeStr,
                    DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        } catch (Exception e) {
            return null;
        }
    }
    
    /**
     * 거래시간을 특정 날짜 기준으로 LocalDateTime 변환
     */
    public LocalDateTime getContractTimeAsLocalDateTime(String baseDate) {
        if (contractTime == null || contractTime.length() != 6 || 
            baseDate == null || baseDate.length() != 8) {
            return null;
        }
        try {
            String dateStr = String.format("%s-%s-%s",
                    baseDate.substring(0, 4),
                    baseDate.substring(4, 6),
                    baseDate.substring(6, 8));
            String timeStr = String.format("%s:%s:%s", 
                    contractTime.substring(0, 2),
                    contractTime.substring(2, 4),
                    contractTime.substring(4, 6));
            return LocalDateTime.parse(dateStr + "T" + timeStr,
                    DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        } catch (Exception e) {
            return null;
        }
    }
    
    /**
     * 상승/하락 여부 확인
     */
    public boolean isRising() {
        if (updateRate == null) {
            return false;
        }
        return updateRate.startsWith("+");
    }
    
    /**
     * 하락 여부 확인
     */
    public boolean isFalling() {
        if (updateRate == null) {
            return false;
        }
        return updateRate.startsWith("-");
    }
    
    /**
     * 변동률을 Double로 변환
     */
    public Double getUpdateRateAsDouble() {
        if (updateRate == null || updateRate.trim().isEmpty()) {
            return 0.0;
        }
        try {
            return Double.parseDouble(updateRate.replace("+", ""));
        } catch (NumberFormatException e) {
            return 0.0;
        }
    }
    
    /**
     * 거래시간 포맷 (HH:MM:SS)
     */
    public String getFormattedContractTime() {
        if (contractTime == null || contractTime.length() != 6) {
            return contractTime;
        }
        return String.format("%s:%s:%s", 
                contractTime.substring(0, 2),
                contractTime.substring(2, 4),
                contractTime.substring(4, 6));
    }
    
    /**
     * 전일지수 대비 등락 포인트 계산
     */
    public BigDecimal getIndexChangePoints() {
        BigDecimal current = getCurrentIndexAsDecimal();
        BigDecimal previous = getPreviousCloseIndexAsDecimal();
        return current.subtract(previous);
    }
    
    /**
     * 업종 시장 활성도 분류 (거래대금 기준)
     */
    public String getMarketActivityLevel() {
        BigDecimal amount = getTradeAmountAsDecimal();
        
        if (amount.compareTo(new BigDecimal("1000000000000")) >= 0) { // 1조 이상
            return "VERY_HIGH";
        } else if (amount.compareTo(new BigDecimal("500000000000")) >= 0) { // 5000억 이상
            return "HIGH";
        } else if (amount.compareTo(new BigDecimal("100000000000")) >= 0) { // 1000억 이상
            return "MEDIUM";
        } else if (amount.compareTo(new BigDecimal("10000000000")) >= 0) { // 100억 이상
            return "LOW";
        } else {
            return "VERY_LOW";
        }
    }
    
    /**
     * 지수 변동 강도 분류
     */
    public String getIndexVolatilityLevel() {
        Double rate = getUpdateRateAsDouble();
        double absRate = Math.abs(rate);
        
        if (absRate >= 3.0) {
            return "EXTREME";     // 3% 이상
        } else if (absRate >= 2.0) {
            return "VERY_HIGH";   // 2-3%
        } else if (absRate >= 1.0) {
            return "HIGH";        // 1-2%
        } else if (absRate >= 0.5) {
            return "MEDIUM";      // 0.5-1%
        } else {
            return "LOW";         // 0.5% 미만
        }
    }
    
    /**
     * 지수 문자열을 BigDecimal로 변환하는 유틸리티
     */
    private BigDecimal parseIndex(String indexStr) {
        if (indexStr == null || indexStr.trim().isEmpty()) {
            return BigDecimal.ZERO;
        }
        try {
            String cleanIndex = indexStr.replaceAll("[+\\-,]", "");
            return new BigDecimal(cleanIndex);
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }
}