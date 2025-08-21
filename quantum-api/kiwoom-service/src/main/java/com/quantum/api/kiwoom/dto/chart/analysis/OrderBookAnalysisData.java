package com.quantum.api.kiwoom.dto.chart.analysis;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.CandleData;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;

/**
 * 거래원별 매물대 데이터
 */
@Data
@Builder
@Schema(description = "거래원별 매물대 데이터")
public class OrderBookAnalysisData {

    @Builder.Default
    private static final String DEFAULT_VALUE = "";
    
    /**
     * 거래원코드
     */
    @JsonProperty("memb_no")
    @Schema(description = "거래원코드", example = "001")
    @Builder.Default
    private String memberNumber = "";
    
    /**
     * 거래원명
     */
    @JsonProperty("memb_nm")
    @Schema(description = "거래원명", example = "대신증권")
    @Builder.Default
    private String memberName = "";
    
    /**
     * 매도수량
     */
    @JsonProperty("sell_qty")
    @Schema(description = "매도수량", example = "1000000")
    @Builder.Default
    private String sellQuantity = "0";
    
    /**
     * 매수수량
     */
    @JsonProperty("buy_qty")
    @Schema(description = "매수수량", example = "500000")
    @Builder.Default
    private String buyQuantity = "0";
    
    /**
     * 순매도수량 (매도 - 매수)
     */
    @JsonProperty("net_qty")
    @Schema(description = "순매도수량", example = "500000")
    @Builder.Default
    private String netQuantity = "0";
    
    /**
     * 매도비율 (%)
     */
    @JsonProperty("sell_rate")
    @Schema(description = "매도비율", example = "15.5")
    @Builder.Default
    private String sellRate = "0.0";
    
    /**
     * 매수비율 (%)
     */
    @JsonProperty("buy_rate")
    @Schema(description = "매수비율", example = "8.2")
    @Builder.Default
    private String buyRate = "0.0";
    
    /**
     * 기본 생성자
     */
    public OrderBookAnalysisData() {}
    
    /**
     * 전체 인자 생성자
     */
    public OrderBookAnalysisData(String memberNumber, String memberName, String sellQuantity, 
                                String buyQuantity, String netQuantity, String sellRate, String buyRate) {
        this.memberNumber = memberNumber;
        this.memberName = memberName;
        this.sellQuantity = sellQuantity;
        this.buyQuantity = buyQuantity;
        this.netQuantity = netQuantity;
        this.sellRate = sellRate;
        this.buyRate = buyRate;
    }
    
    /**
     * 매도수량을 Long으로 변환
     */
    public long getSellQuantityAsLong() {
        return parseLongSafely(sellQuantity);
    }
    
    /**
     * 매수수량을 Long으로 변환
     */
    public long getBuyQuantityAsLong() {
        return parseLongSafely(buyQuantity);
    }
    
    /**
     * 순매도수량을 Long으로 변환
     */
    public long getNetQuantityAsLong() {
        return parseLongSafely(netQuantity);
    }
    
    /**
     * 매도비율을 Double로 변환
     */
    public double getSellRateAsDouble() {
        return parseDoubleSafely(sellRate);
    }
    
    /**
     * 매수비율을 Double로 변환
     */
    public double getBuyRateAsDouble() {
        return parseDoubleSafely(buyRate);
    }
    
    /**
     * 매도수량을 BigDecimal로 변환
     */
    public BigDecimal getSellQuantityAsDecimal() {
        return parseBigDecimalSafely(sellQuantity);
    }
    
    /**
     * 매수수량을 BigDecimal로 변환
     */
    public BigDecimal getBuyQuantityAsDecimal() {
        return parseBigDecimalSafely(buyQuantity);
    }
    
    /**
     * 순매도 여부 (순매도수량 > 0)
     */
    public boolean isNetSelling() {
        return getNetQuantityAsLong() > 0;
    }
    
    /**
     * 순매수 여부 (순매도수량 < 0)
     */
    public boolean isNetBuying() {
        return getNetQuantityAsLong() < 0;
    }
    
    /**
     * 거래원 주도성 분류
     */
    public String getDominanceLevel() {
        double sellRate = getSellRateAsDouble();
        double buyRate = getBuyRateAsDouble();
        double maxRate = Math.max(sellRate, buyRate);
        
        if (maxRate >= 20.0) return "VERY_HIGH";
        if (maxRate >= 10.0) return "HIGH";
        if (maxRate >= 5.0) return "MEDIUM";
        if (maxRate >= 1.0) return "LOW";
        return "VERY_LOW";
    }
    
    /**
     * 매도/매수 비율 (매도 기준)
     */
    public double getSellToBuyRatio() {
        long buyQty = getBuyQuantityAsLong();
        if (buyQty == 0) {
            return getSellQuantityAsLong() > 0 ? Double.POSITIVE_INFINITY : 0.0;
        }
        return (double) getSellQuantityAsLong() / buyQty;
    }
    
    /**
     * CandleData로 변환 (매도/매수 정보를 가격 정보로 대체)
     */
    public CandleData toCandleData() {
        return CandleData.builder()
                .currentPrice(String.valueOf(getSellQuantityAsLong()))
                .openPrice(String.valueOf(getBuyQuantityAsLong()))
                .highPrice(String.valueOf(Math.max(getSellQuantityAsLong(), getBuyQuantityAsLong())))
                .lowPrice(String.valueOf(Math.min(getSellQuantityAsLong(), getBuyQuantityAsLong())))
                .tradeQuantity(String.valueOf(Math.abs(getNetQuantityAsLong())))
                .build();
    }
    
    // 유틸리티 메소드들
    private long parseLongSafely(String value) {
        if (value == null || value.trim().isEmpty()) {
            return 0L;
        }
        try {
            return Long.parseLong(value.replace(",", "").replace("+", "").replace("-", ""));
        } catch (NumberFormatException e) {
            return 0L;
        }
    }
    
    private double parseDoubleSafely(String value) {
        if (value == null || value.trim().isEmpty()) {
            return 0.0;
        }
        try {
            return Double.parseDouble(value.replace("+", ""));
        } catch (NumberFormatException e) {
            return 0.0;
        }
    }
    
    private BigDecimal parseBigDecimalSafely(String value) {
        if (value == null || value.trim().isEmpty()) {
            return BigDecimal.ZERO;
        }
        try {
            return new BigDecimal(value.replace(",", "").replace("+", ""));
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }
}
