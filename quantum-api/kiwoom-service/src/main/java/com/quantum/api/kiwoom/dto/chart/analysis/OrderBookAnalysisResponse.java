package com.quantum.api.kiwoom.dto.chart.analysis;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.BaseChartResponse;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;

import java.util.List;

/**
 * 키움증권 거래원매물대분석응답 (ka10043) DTO
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "거래원매물대분석응답 (ka10043)")
public class OrderBookAnalysisResponse extends BaseChartResponse {
    
    /**
     * 종목코드
     */
    @JsonProperty("stk_cd")
    @Schema(description = "종목코드", example = "005930")
    private String stockCode;
    
    /**
     * 종목명
     */
    @JsonProperty("stk_nm")
    @Schema(description = "종목명", example = "삼성전자")
    private String stockName;
    
    /**
     * 기준일자
     */
    @JsonProperty("base_dt")
    @Schema(description = "기준일자", example = "20241108")
    private String baseDate;
    
    /**
     * 거래원별 매물대 데이터 리스트
     */
    @JsonProperty("output")
    @Schema(description = "거래원별 매물대 데이터")
    @Builder.Default
    private List<OrderBookAnalysisData> orderBookData = List.of();
    
    /**
     * 기본 생성자
     */
    public OrderBookAnalysisResponse() {
        super();
    }
    
    /**
     * 데이터 없음 여부 확인
     */
    public boolean hasOrderBookData() {
        return orderBookData != null && !orderBookData.isEmpty();
    }
    
    /**
     * 데이터 개수 반환
     */
    public int getOrderBookDataCount() {
        return orderBookData != null ? orderBookData.size() : 0;
    }
    
    /**
     * 전체 매도수량 합계
     */
    public long getTotalSellQuantity() {
        return orderBookData.stream()
                .mapToLong(OrderBookAnalysisData::getSellQuantityAsLong)
                .sum();
    }
    
    /**
     * 전체 매수수량 합계
     */
    public long getTotalBuyQuantity() {
        return orderBookData.stream()
                .mapToLong(OrderBookAnalysisData::getBuyQuantityAsLong)
                .sum();
    }
    
    /**
     * 매도/매수 비율 (매도 기준)
     */
    public double getSellToBuyRatio() {
        long buyQuantity = getTotalBuyQuantity();
        if (buyQuantity == 0) {
            return 0.0;
        }
        return (double) getTotalSellQuantity() / buyQuantity;
    }
    
    /**
     * 상위 N개 거래원 매물대 데이터 반환
     */
    public List<OrderBookAnalysisData> getTopOrderBookData(int limit) {
        if (orderBookData == null || orderBookData.isEmpty()) {
            return List.of();
        }
        
        return orderBookData.stream()
                .limit(Math.min(limit, orderBookData.size()))
                .toList();
    }
}
