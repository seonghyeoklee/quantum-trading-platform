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
 * 키움증권 주식년봉차트조회요청 (ka10094) 응답 DTO
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "주식년봉차트조회 응답")
public class YearlyChartResponse extends BaseChartResponse {
    
    /**
     * 종목코드
     */
    @JsonProperty("stk_cd")
    @Schema(description = "종목코드", example = "005930")
    private String stockCode;
    
    /**
     * 주식년봉차트조회 데이터 리스트
     */
    @JsonProperty("stk_yr_pole_chart_qry")
    @Schema(description = "년봉 차트 데이터 목록")
    private List<YearlyChartData> chartData;
    
    /**
     * 기본 생성자 (Jackson 역직렬화용)
     */
    public YearlyChartResponse() {
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
                .map(YearlyChartData::toCandleData)
                .collect(Collectors.toList());
    }
    
    /**
     * 첫 번째 (최신) 데이터 반환
     */
    public YearlyChartData getLatestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(0);
    }
    
    /**
     * 마지막 (가장 오래된) 데이터 반환
     */
    public YearlyChartData getOldestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(chartData.size() - 1);
    }
    
    /**
     * 특정 년도의 데이터 조회
     */
    public YearlyChartData getDataByYear(int year) {
        if (isEmpty()) {
            return null;
        }
        
        return chartData.stream()
                .filter(data -> {
                    Integer dataYear = data.getYear();
                    return dataYear != null && dataYear == year;
                })
                .findFirst()
                .orElse(null);
    }
    
    /**
     * 특정 년도 범위의 데이터 필터링
     */
    public List<YearlyChartData> getDataByYearRange(int startYear, int endYear) {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(data -> {
                    Integer dataYear = data.getYear();
                    return dataYear != null && 
                           dataYear >= startYear && 
                           dataYear <= endYear;
                })
                .collect(Collectors.toList());
    }
}