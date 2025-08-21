package com.quantum.api.kiwoom.dto.chart.common;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * OHLCV 캔들 차트 공통 데이터
 * 모든 시간대별 차트에서 공통으로 사용
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "캔들 차트 데이터 (OHLCV)")
public class CandleData {
    
    /**
     * 현재가 (종가)
     */
    @JsonProperty("cur_prc")
    @Schema(description = "현재가(종가)", example = "133600")
    private String currentPrice;
    
    /**
     * 시가
     */
    @JsonProperty("open_pric")
    @Schema(description = "시가", example = "133600")
    private String openPrice;
    
    /**
     * 고가
     */
    @JsonProperty("high_pric")
    @Schema(description = "고가", example = "134000")
    private String highPrice;
    
    /**
     * 저가
     */
    @JsonProperty("low_pric")
    @Schema(description = "저가", example = "133000")
    private String lowPrice;
    
    /**
     * 거래량
     */
    @JsonProperty("trde_qty")
    @Schema(description = "거래량", example = "1000000")
    private String tradeQuantity;
    
    /**
     * 거래대금 (일봉, 주봉, 년봉만)
     */
    @JsonProperty("trde_prica")
    @Schema(description = "거래대금", example = "133600000000")
    private String tradeAmount;
    
    /**
     * 일자 (일봉, 주봉, 년봉)
     */
    @JsonProperty("dt")
    @Schema(description = "일자", example = "20241107")
    private String date;
    
    /**
     * 체결시간 (틱, 분봉)
     */
    @JsonProperty("cntr_tm")
    @Schema(description = "체결시간", example = "20241106141800")
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
     * 전일종가
     */
    @JsonProperty("pred_close_pric")
    @Schema(description = "전일종가", example = "132800")
    private String previousClosePrice;
    
    // ===== 유틸리티 메서드 =====
    
    /**
     * 현재가를 BigDecimal로 변환
     */
    public BigDecimal getCurrentPriceAsDecimal() {
        return parsePrice(currentPrice);
    }
    
    /**
     * 시가를 BigDecimal로 변환
     */
    public BigDecimal getOpenPriceAsDecimal() {
        return parsePrice(openPrice);
    }
    
    /**
     * 고가를 BigDecimal로 변환
     */
    public BigDecimal getHighPriceAsDecimal() {
        return parsePrice(highPrice);
    }
    
    /**
     * 저가를 BigDecimal로 변환
     */
    public BigDecimal getLowPriceAsDecimal() {
        return parsePrice(lowPrice);
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
     * 일자를 LocalDate로 변환
     */
    public LocalDate getDateAsLocalDate() {
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
     * 체결시간을 LocalDateTime으로 변환
     */
    public LocalDateTime getContractTimeAsLocalDateTime() {
        if (contractTime == null || contractTime.length() != 14) {
            return null;
        }
        try {
            return LocalDateTime.parse(contractTime, DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        } catch (Exception e) {
            return null;
        }
    }
    
    /**
     * 상승/하락 여부 확인 (전일 대비)
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
     * 가격 문자열을 BigDecimal로 변환하는 유틸리티
     */
    private BigDecimal parsePrice(String priceStr) {
        if (priceStr == null || priceStr.trim().isEmpty()) {
            return BigDecimal.ZERO;
        }
        try {
            // +, - 기호 제거하고 숫자만 추출
            String cleanPrice = priceStr.replaceAll("[+\\-,]", "");
            return new BigDecimal(cleanPrice);
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }
}