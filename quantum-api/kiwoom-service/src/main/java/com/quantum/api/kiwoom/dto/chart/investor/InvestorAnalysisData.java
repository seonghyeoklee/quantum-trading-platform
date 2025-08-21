package com.quantum.api.kiwoom.dto.chart.investor;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.CandleData;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 투자자별 거래 데이터
 */
@Data
@Builder
@Schema(description = "투자자별 거래 데이터")
public class InvestorAnalysisData {

    @Builder.Default
    private static final String DEFAULT_VALUE = "";
    
    /**
     * 일자
     */
    @JsonProperty("dt")
    @Schema(description = "일자", example = "20241108")
    @Builder.Default
    private String date = "";
    
    /**
     * 투자자 구분
     * 01: 개인, 02: 기관, 03: 외국인, 04: 기타법인
     */
    @JsonProperty("investor_tp")
    @Schema(description = "투자자 구분", example = "01")
    @Builder.Default
    private String investorType = "01";
    
    /**
     * 투자자명
     */
    @JsonProperty("investor_nm")
    @Schema(description = "투자자명", example = "개인")
    @Builder.Default
    private String investorName = "";
    
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
    @Schema(description = "매수수량", example = "1500000")
    @Builder.Default
    private String buyQuantity = "0";
    
    /**
     * 순매수수량 (매수 - 매도)
     */
    @JsonProperty("net_buy_qty")
    @Schema(description = "순매수수량", example = "500000")
    @Builder.Default
    private String netBuyQuantity = "0";
    
    /**
     * 거래대금
     */
    @JsonProperty("trade_amt")
    @Schema(description = "거래대금", example = "67800000000")
    @Builder.Default
    private String tradeAmount = "0";
    
    /**
     * 비중 (%)
     */
    @JsonProperty("rate")
    @Schema(description = "비중", example = "25.5")
    @Builder.Default
    private String rate = "0.0";
    
    /**
     * 기본 생성자
     */
    public InvestorAnalysisData() {}
    
    /**
     * 전체 인자 생성자
     */
    public InvestorAnalysisData(String date, String investorType, String investorName, String sellQuantity, 
                              String buyQuantity, String netBuyQuantity, String tradeAmount, String rate) {
        this.date = date;
        this.investorType = investorType;
        this.investorName = investorName;
        this.sellQuantity = sellQuantity;
        this.buyQuantity = buyQuantity;
        this.netBuyQuantity = netBuyQuantity;
        this.tradeAmount = tradeAmount;
        this.rate = rate;
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
     * 순매수수량을 Long으로 변환
     */
    public long getNetBuyQuantityAsLong() {
        return parseLongSafely(netBuyQuantity);
    }
    
    /**
     * 거래대금을 Long으로 변환
     */
    public long getTradeAmountAsLong() {
        return parseLongSafely(tradeAmount);
    }
    
    /**
     * 비중을 Double로 변환
     */
    public double getRateAsDouble() {
        return parseDoubleSafely(rate);
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
     * 거래대금을 BigDecimal로 변환
     */
    public BigDecimal getTradeAmountAsDecimal() {
        return parseBigDecimalSafely(tradeAmount);
    }
    
    /**
     * 날짜를 LocalDate로 변환
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
     * 순매수 여부 (순매수수량 > 0)
     */
    public boolean isNetBuying() {
        return getNetBuyQuantityAsLong() > 0;
    }
    
    /**
     * 순매도 여부 (순매수수량 < 0)
     */
    public boolean isNetSelling() {
        return getNetBuyQuantityAsLong() < 0;
    }
    
    /**
     * 개인 투자자 여부
     */
    public boolean isIndividualInvestor() {
        return "01".equals(investorType);
    }
    
    /**
     * 기관 투자자 여부
     */
    public boolean isInstitutionalInvestor() {
        return "02".equals(investorType);
    }
    
    /**
     * 외국인 투자자 여부
     */
    public boolean isForeignInvestor() {
        return "03".equals(investorType);
    }
    
    /**
     * 기타법인 여부
     */
    public boolean isOtherCorporation() {
        return "04".equals(investorType);
    }
    
    /**
     * 주요 투자자 여부 (개인, 기관, 외국인)
     */
    public boolean isMajorInvestor() {
        return isIndividualInvestor() || isInstitutionalInvestor() || isForeignInvestor();
    }
    
    /**
     * 투자자 영향력 분류
     */
    public String getInfluenceLevel() {
        double rate = getRateAsDouble();
        
        if (rate >= 30.0) return "VERY_HIGH";
        if (rate >= 20.0) return "HIGH";
        if (rate >= 10.0) return "MEDIUM";
        if (rate >= 5.0) return "LOW";
        return "VERY_LOW";
    }
    
    /**
     * 거래 규모 분류
     */
    public String getTradingSizeCategory() {
        long tradeAmount = getTradeAmountAsLong();
        
        if (tradeAmount >= 1_000_000_000_000L) return "TRILLION";      // 1조 이상
        if (tradeAmount >= 100_000_000_000L) return "HUNDRED_BILLION"; // 1000억 이상
        if (tradeAmount >= 10_000_000_000L) return "TEN_BILLION";      // 100억 이상
        if (tradeAmount >= 1_000_000_000L) return "BILLION";           // 10억 이상
        if (tradeAmount >= 100_000_000L) return "HUNDRED_MILLION";     // 1억 이상
        return "SMALL";
    }
    
    /**
     * CandleData로 변환 (매도/매수 정보를 가격 정보로 대체)
     */
    public CandleData toCandleData() {
        long sellQty = getSellQuantityAsLong();
        long buyQty = getBuyQuantityAsLong();
        long netBuyQty = getNetBuyQuantityAsLong();
        
        return CandleData.builder()
                .date(date)
                .openPrice(String.valueOf(buyQty))
                .highPrice(String.valueOf(Math.max(sellQty, buyQty)))
                .lowPrice(String.valueOf(Math.min(sellQty, buyQty)))
                .currentPrice(String.valueOf(Math.abs(netBuyQty)))
                .tradeQuantity(String.valueOf(Math.abs(netBuyQty)))
                .tradeAmount(tradeAmount)
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
