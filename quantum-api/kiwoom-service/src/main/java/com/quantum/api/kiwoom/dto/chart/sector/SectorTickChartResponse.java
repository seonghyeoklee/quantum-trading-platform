package com.quantum.api.kiwoom.dto.chart.sector;

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
 * 키움증권 업종틱차트조회요청 (ka20004) 응답 DTO
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "업종틱차트조회 응답")
public class SectorTickChartResponse extends BaseChartResponse {
    
    /**
     * 업종코드
     */
    @JsonProperty("upjong_cd")
    @Schema(description = "업종코드", example = "0001")
    private String sectorCode;
    
    /**
     * 업종틱차트조회 데이터 리스트
     */
    @JsonProperty("upjong_tic_chart_qry")
    @Schema(description = "업종틱차트 데이터 목록")
    private List<SectorTickChartData> chartData;
    
    /**
     * 기본 생성자 (Jackson 역직렬화용)
     */
    public SectorTickChartResponse() {
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
                .map(SectorTickChartData::toCandleData)
                .collect(Collectors.toList());
    }
    
    /**
     * 첫 번째 (최신) 데이터 반환
     */
    public SectorTickChartData getLatestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(0);
    }
    
    /**
     * 마지막 (가장 오래된) 데이터 반환
     */
    public SectorTickChartData getOldestData() {
        if (isEmpty()) {
            return null;
        }
        return chartData.get(chartData.size() - 1);
    }
    
    /**
     * 특정 시간대의 업종 틱 데이터 필터링
     */
    public List<SectorTickChartData> getDataByTimeRange(String startTime, String endTime) {
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
     * 정규 거래시간 업종 틱 데이터만 필터링 (09:00 ~ 15:30)
     */
    public List<SectorTickChartData> getRegularTradingHoursData() {
        return getDataByTimeRange("090000", "153000");
    }
    
    /**
     * 상승 업종 틱 데이터만 필터링
     */
    public List<SectorTickChartData> getRisingSectorTicksData() {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(SectorTickChartData::isRising)
                .collect(Collectors.toList());
    }
    
    /**
     * 하락 업종 틱 데이터만 필터링
     */
    public List<SectorTickChartData> getFallingSectorTicksData() {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(SectorTickChartData::isFalling)
                .collect(Collectors.toList());
    }
    
    /**
     * 고활성 업종 틱 데이터 필터링 (거래대금 기준)
     */
    public List<SectorTickChartData> getHighActivitySectorTicksData() {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(data -> {
                    String activityLevel = data.getMarketActivityLevel();
                    return "HIGH".equals(activityLevel) || "VERY_HIGH".equals(activityLevel);
                })
                .collect(Collectors.toList());
    }
    
    /**
     * 고변동성 업종 틱 데이터 필터링
     */
    public List<SectorTickChartData> getHighVolatilitySectorTicksData() {
        if (isEmpty()) {
            return List.of();
        }
        
        return chartData.stream()
                .filter(data -> {
                    String volatilityLevel = data.getIndexVolatilityLevel();
                    return "HIGH".equals(volatilityLevel) || 
                           "VERY_HIGH".equals(volatilityLevel) || 
                           "EXTREME".equals(volatilityLevel);
                })
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
                .mapToLong(SectorTickChartData::getTradeQuantityAsLong)
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
                .map(SectorTickChartData::getTradeAmountAsDecimal)
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
                .mapToLong(SectorTickChartData::getTradeQuantityAsLong)
                .average()
                .orElse(0.0);
    }
    
    /**
     * 최고 지수
     */
    public BigDecimal getHighestIndex() {
        if (isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return chartData.stream()
                .map(SectorTickChartData::getCurrentIndexAsDecimal)
                .max(BigDecimal::compareTo)
                .orElse(BigDecimal.ZERO);
    }
    
    /**
     * 최저 지수
     */
    public BigDecimal getLowestIndex() {
        if (isEmpty()) {
            return BigDecimal.ZERO;
        }
        
        return chartData.stream()
                .map(SectorTickChartData::getCurrentIndexAsDecimal)
                .min(BigDecimal::compareTo)
                .orElse(BigDecimal.ZERO);
    }
    
    /**
     * 업종 표시명 반환 (sectorCode 기반)
     */
    public String getSectorDisplayName() {
        if (isEmpty()) {
            return "알 수 없는 업종";
        }
        
        // 첫 번째 데이터에서 업종 정보를 추출하거나 코드 기반으로 반환
        SectorTickChartData firstData = chartData.get(0);
        if (firstData.getSectorInfo() != null && !firstData.getSectorInfo().trim().isEmpty()) {
            return firstData.getSectorInfo();
        }
        
        // 코드 기반 매핑
        switch (sectorCode) {
            case "0001": return "코스피";
            case "1001": return "코스닥";
            case "2001": return "코스피200";
            case "0002": return "대형주";
            case "0003": return "중형주";
            case "0004": return "소형주";
            default: return "업종-" + sectorCode;
        }
    }
}