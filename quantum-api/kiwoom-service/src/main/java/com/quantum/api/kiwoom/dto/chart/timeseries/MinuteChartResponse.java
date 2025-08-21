package com.quantum.api.kiwoom.dto.chart.timeseries;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.BaseChartResponse;
import com.quantum.api.kiwoom.dto.chart.common.CandleData;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 키움증권 주식분봉차트조회요청 (ka10080) 응답 DTO
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "주식분봉차트조회 응답")
public class MinuteChartResponse extends BaseChartResponse {
    
    /**
     * 종목코드
     */
    @JsonProperty("stk_cd")
    @Schema(description = "종목코드", example = "005930")
    private String stockCode;
    
    /**
     * 주식분봉차트조회 데이터 리스트
     */
    @JsonProperty("stk_min_pole_chart_qry")
    @Schema(description = "분봉 차트 데이터 목록")
    private List<MinuteChartData> chartData;
    
    /**
     * 기본 생성자 (Jackson 역직렬화용)
     */
    public MinuteChartResponse() {
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
                .map(MinuteChartData::toCandleData)
                .collect(Collectors.toList());
    }
    
    /**
     * 첫 번째 (최신) 데이터 반환
     */
    public MinuteChartData getLatestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(0);
    }
    
    /**
     * 마지막 (가장 오래된) 데이터 반환
     */
    public MinuteChartData getOldestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(chartData.size() - 1);
    }
    
    /**
     * 특정 시간대의 데이터 필터링
     */
    public List<MinuteChartData> getDataByTimeRange(String startTime, String endTime) {
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
     * 정규 거래시간 데이터만 필터링 (09:00 ~ 15:30)
     */
    public List<MinuteChartData> getRegularTradingHoursData() {
        return getDataByTimeRange("090000", "153000");
    }
    
    /**
     * 장 시작 후 첫 거래 데이터
     */
    public MinuteChartData getFirstTradingData() {
        List<MinuteChartData> regularData = getRegularTradingHoursData();
        if (regularData.isEmpty()) {
            return null;
        }
        return regularData.get(regularData.size() - 1); // 오래된 순서로 정렬되어 있다고 가정
    }
    
    /**
     * 장 마감 직전 마지막 거래 데이터
     */
    public MinuteChartData getLastTradingData() {
        List<MinuteChartData> regularData = getRegularTradingHoursData();
        if (regularData.isEmpty()) {
            return null;
        }
        return regularData.get(0); // 최신 순서로 정렬되어 있다고 가정
    }
}