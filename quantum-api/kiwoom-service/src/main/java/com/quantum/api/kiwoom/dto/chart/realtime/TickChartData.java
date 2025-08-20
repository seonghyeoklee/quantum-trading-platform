package com.quantum.api.kiwoom.dto.chart.realtime;

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
 * 틱차트 개별 데이터
 * 키움 API stk_tic_chart_qry 배열의 각 요소
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "틱차트 개별 데이터")
public class TickChartData {
    
    /**
     * 현재가
     */
    @JsonProperty("cur_prc")
    @Schema(description = "현재가", example = "133600")
    private String currentPrice;
    
    /**
     * 거래량
     */
    @JsonProperty("trde_qty")
    @Schema(description = "거래량", example = "1000")
    private String tradeQuantity;
    
    /**
     * 거래대금
     */
    @JsonProperty("trde_prica")
    @Schema(description = "거래대금", example = "133600000")
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
     * 종목정보
     */
    @JsonProperty("stk_infr")
    @Schema(description = "종목정보")
    private String stockInfo;
    
    /**
     * 수정주가이벤트
     */
    @JsonProperty("upd_stkpc_event")
    @Schema(description = "수정주가이벤트")
    private String updateStockPriceEvent;
    
    /**
     * 전일종가
     */
    @JsonProperty("pred_close_pric")
    @Schema(description = "전일종가", example = "132800")
    private String previousClosePrice;
    
    // ===== 유틸리티 메서드 =====
    
    /**
     * 공통 CandleData로 변환 (틱은 OHLC가 모두 현재가)
     */
    public CandleData toCandleData() {
        return CandleData.builder()
                .currentPrice(currentPrice)
                .openPrice(currentPrice)       // 틱은 시가 = 현재가
                .highPrice(currentPrice)       // 틱은 고가 = 현재가
                .lowPrice(currentPrice)        // 틱은 저가 = 현재가
                .tradeQuantity(tradeQuantity)
                .tradeAmount(tradeAmount)
                .date(contractTime) // 틱은 시간 정보 사용
                .updateStockPriceType(updateStockPriceType)
                .updateRate(updateRate)
                .previousClosePrice(previousClosePrice)
                .build();
    }
    
    /**
     * 현재가를 BigDecimal로 변환
     */
    public BigDecimal getCurrentPriceAsDecimal() {
        return parsePrice(currentPrice);
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
        return parsePrice(tradeAmount);
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
     * 틱 거래 규모 분류
     */
    public String getTickSizeCategory() {
        Long quantity = getTradeQuantityAsLong();
        if (quantity == 0) {
            return "UNKNOWN";
        } else if (quantity < 1000) {
            return "SMALL";      // 1000주 미만
        } else if (quantity < 10000) {
            return "MEDIUM";     // 1000-9999주
        } else if (quantity < 100000) {
            return "LARGE";      // 10000-99999주
        } else {
            return "EXTRA_LARGE"; // 100000주 이상
        }
    }
    
    /**
     * 전일종가 대비 등락액 계산
     */
    public BigDecimal getPriceChangeAmount() {
        BigDecimal current = getCurrentPriceAsDecimal();
        BigDecimal previous = parsePrice(previousClosePrice);
        return current.subtract(previous);
    }
    
    /**
     * 가격 문자열을 BigDecimal로 변환하는 유틸리티
     */
    private BigDecimal parsePrice(String priceStr) {
        if (priceStr == null || priceStr.trim().isEmpty()) {
            return BigDecimal.ZERO;
        }
        try {
            String cleanPrice = priceStr.replaceAll("[+\\-,]", "");
            return new BigDecimal(cleanPrice);
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }
}