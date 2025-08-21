package com.quantum.api.kiwoom.dto.sector.chart;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.sector.common.BaseSectorRequest;
import com.quantum.api.kiwoom.dto.sector.common.SectorApiType;
import com.quantum.api.kiwoom.dto.sector.common.SectorCode;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

/**
 * 업종일봉조회요청 (ka20006) - 업종의 일봉 차트 데이터 조회
 * 
 * 특정 업종의 일봉 단위 시세 데이터를 조회합니다.
 * 지정한 기간의 업종 지수 일봉 데이터를 제공합니다.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = false)
public class SectorDailyChartRequest extends BaseSectorRequest {
    
    private static final String API_ID = "ka20006";
    
    /**
     * 업종코드 (필수)
     * 예: "001" (종합KOSPI), "101" (종합KOSDAQ)
     */
    @JsonProperty("FID_COND_MRKT_DIV_CODE")
    private String sectorCode;
    
    /**
     * 조회 시작일자 (YYYYMMDD) (필수)
     */
    @JsonProperty("FID_INPUT_DATE_1")
    private String fromDate;
    
    /**
     * 조회 종료일자 (YYYYMMDD) (필수)
     */
    @JsonProperty("FID_INPUT_DATE_2")
    private String toDate;
    
    /**
     * 수정주가반영구분
     * 0: 수정주가 미반영, 1: 수정주가 반영 (기본값: 1)
     */
    @JsonProperty("FID_ORG_ADJ_PRC")
    private String adjustedPriceFlag;
    
    /**
     * 기간분류
     * D: 일봉, W: 주봉, M: 월봉 (기본값: D)
     */
    @JsonProperty("FID_PERIOD_DIV_CODE")
    private String periodType;
    
    @Override
    public SectorApiType getApiType() {
        return SectorApiType.SECTOR_CHART;
    }
    
    @Override
    public String getApiId() {
        return API_ID;
    }
    
    @Override
    public void validate() {
        super.validate();
        
        if (sectorCode == null || sectorCode.trim().isEmpty()) {
            throw new IllegalArgumentException("업종코드는 필수입니다.");
        }
        
        // 업종코드 유효성 검증
        try {
            SectorCode.fromCode(sectorCode);
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("올바르지 않은 업종코드입니다: " + sectorCode);
        }
        
        if (fromDate == null || fromDate.trim().isEmpty()) {
            throw new IllegalArgumentException("조회 시작일자는 필수입니다.");
        }
        
        if (toDate == null || toDate.trim().isEmpty()) {
            throw new IllegalArgumentException("조회 종료일자는 필수입니다.");
        }
        
        // 날짜 형식 검증
        if (!fromDate.matches("\\d{8}")) {
            throw new IllegalArgumentException("조회 시작일자는 YYYYMMDD 형식이어야 합니다.");
        }
        
        if (!toDate.matches("\\d{8}")) {
            throw new IllegalArgumentException("조회 종료일자는 YYYYMMDD 형식이어야 합니다.");
        }
        
        // 시작일자가 종료일자보다 늦으면 안됨
        if (fromDate.compareTo(toDate) > 0) {
            throw new IllegalArgumentException("시작일자가 종료일자보다 늦을 수 없습니다.");
        }
        
        // 기본값 설정
        if (adjustedPriceFlag == null) {
            adjustedPriceFlag = "1"; // 수정주가 반영
        }
        
        if (periodType == null) {
            periodType = "D"; // 일봉
        }
        
        // 기간분류 유효성 검증
        if (!isValidPeriodType(periodType)) {
            throw new IllegalArgumentException("지원하지 않는 기간분류입니다. 지원: D(일봉), W(주봉), M(월봉)");
        }
    }
    
    /**
     * 지원하는 기간분류인지 확인
     */
    private boolean isValidPeriodType(String periodType) {
        return "D".equals(periodType) || "W".equals(periodType) || "M".equals(periodType);
    }
    
    /**
     * 편의 메서드: 업종코드 설정
     */
    public static SectorDailyChartRequestBuilder withSectorCode(String sectorCode) {
        return builder().sectorCode(sectorCode);
    }
    
    /**
     * 편의 메서드: 일봉 차트 요청
     */
    public static SectorDailyChartRequestBuilder dailyChart(String sectorCode, String fromDate, String toDate) {
        return builder()
                .sectorCode(sectorCode)
                .fromDate(fromDate)
                .toDate(toDate)
                .periodType("D");
    }
    
    /**
     * 편의 메서드: 주봉 차트 요청
     */
    public static SectorDailyChartRequestBuilder weeklyChart(String sectorCode, String fromDate, String toDate) {
        return builder()
                .sectorCode(sectorCode)
                .fromDate(fromDate)
                .toDate(toDate)
                .periodType("W");
    }
    
    /**
     * 편의 메서드: 월봉 차트 요청
     */
    public static SectorDailyChartRequestBuilder monthlyChart(String sectorCode, String fromDate, String toDate) {
        return builder()
                .sectorCode(sectorCode)
                .fromDate(fromDate)
                .toDate(toDate)
                .periodType("M");
    }
}