package com.quantum.api.kiwoom.dto.chart.realtime;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.BaseChartResponse;
import com.quantum.api.kiwoom.dto.chart.common.CandleData;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 키움증권 주식틱차트조회요청 (ka10079) 응답 DTO
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "주식틱차트조회 응답")
public class TickChartResponse extends BaseChartResponse {
    
    /**
     * 종목코드
     */
    @JsonProperty("stk_cd")
    @Schema(description = "종목코드", example = "005930")
    private String stockCode;
    
    /**
     * 주식틱차트조회 데이터 리스트
     */
    @JsonProperty("stk_tic_chart_qry")
    @Schema(description = "틱차트 데이터 목록")
    private List<TickChartData> chartData;
    
    /**
     * 기본 생성자 (Jackson 역직렬화용)
     */
    public TickChartResponse() {
        super();
    }
    
    /**
     * 차트 데이터 개수 반환
     */
    public int getDataSize() {
        return chartData != null ? chartData.size() : 0;
    }
    
    /**
     * 빈 데이터 여부 확인
     */
    public boolean isEmpty() {
        return chartData == null || chartData.isEmpty();
    }
    
    /**
     * 차트 데이터를 공통 CandleData 형태로 변환
     */
    public List<CandleData> toCandleDataList() {
        if (chartData == null) {
            return List.of();
        }
        
        return chartData.stream()
                .map(TickChartData::toCandleData)
                .collect(Collectors.toList());
    }
    
    /**
     * 첫 번째 (최신) 데이터 반환
     */
    public TickChartData getLatestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(0);
    }
    
    /**
     * 마지막 (가장 오래된) 데이터 반환
     */
    public TickChartData getOldestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(chartData.size() - 1);
    }
    
    /**
     * 특정 시간대의 틱 데이터 필터링
     */
    public List<TickChartData> getDataByTimeRange(String startTime, String endTime) {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(data -> {
                    String time = data.getContractTime();
                    return time != null && 
                           time.compareTo(startTime) >= 0 && 
                           time.compareTo(endTime) <= 0;
                })
                .collect(Collectors.toList());
    }
    
    /**
     * 정규 거래시간 틱 데이터만 필터링 (09:00 ~ 15:30)
     */
    public List<TickChartData> getRegularTradingHoursData() {
        return getDataByTimeRange("090000", "153000");
    }
    
    /**
     * 상승 틱 데이터만 필터링
     */
    public List<TickChartData> getRisingTicksData() {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(TickChartData::isRising)
                .collect(Collectors.toList());
    }
    
    /**
     * 하락 틱 데이터만 필터링
     */
    public List<TickChartData> getFallingTicksData() {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(TickChartData::isFalling)
                .collect(Collectors.toList());
    }
    
    /**
     * 대량 거래 틱 데이터 필터링 (10,000주 이상)
     */
    public List<TickChartData> getLargeVolumeTicksData() {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(data -> data.getTradeQuantityAsLong() >= 10000)
                .collect(Collectors.toList());
    }
    
    /**
     * 특정 가격 이상의 틱 데이터 필터링
     */
    public List<TickChartData> getDataByMinPrice(BigDecimal minPrice) {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(data -> data.getCurrentPriceAsDecimal().compareTo(minPrice) >= 0)
                .collect(Collectors.toList());
    }
    
    /**
     * 총 거래량 합계
     */
    public Long getTotalTradeQuantity() {
        if (isEmpty()) {
            return 0L;
        }
        
        return chartData.stream()
                .mapToLong(TickChartData::getTradeQuantityAsLong)
                .sum();
    }
    
    /**
     * 총 거래대금 합계
     */
    public BigDecimal getTotalTradeAmount() {
        if (isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return chartData.stream()
                .map(TickChartData::getTradeAmountAsDecimal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
    
    /**
     * 평균 거래량
     */
    public Double getAverageTradeQuantity() {
        if (isEmpty()) {
            return 0.0;
        }
        
        return chartData.stream()
                .mapToLong(TickChartData::getTradeQuantityAsLong)
                .average()
                .orElse(0.0);
    }
}