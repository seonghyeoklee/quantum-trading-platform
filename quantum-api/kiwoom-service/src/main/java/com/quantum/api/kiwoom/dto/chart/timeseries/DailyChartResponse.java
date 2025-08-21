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
 * 키움증권 주식일봉차트조회요청 (ka10081) 응답 DTO
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "주식일봉차트조회 응답")
public class DailyChartResponse extends BaseChartResponse {
    
    /**
     * 종목코드
     */
    @JsonProperty("stk_cd")
    @Schema(description = "종목코드", example = "005930")
    private String stockCode;
    
    /**
     * 주식일봉차트조회 데이터 리스트
     */
    @JsonProperty("stk_dt_pole_chart_qry")
    @Schema(description = "일봉 차트 데이터 목록")
    private List<DailyChartData> chartData;
    
    /**
     * 기본 생성자 (Jackson 역직렬화용)
     */
    public DailyChartResponse() {
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
                .map(DailyChartData::toCandleData)
                .collect(Collectors.toList());
    }
    
    /**
     * 첫 번째 (최신) 데이터 반환
     */
    public DailyChartData getLatestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(0);
    }
    
    /**
     * 마지막 (가장 오래된) 데이터 반환
     */
    public DailyChartData getOldestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(chartData.size() - 1);
    }
}