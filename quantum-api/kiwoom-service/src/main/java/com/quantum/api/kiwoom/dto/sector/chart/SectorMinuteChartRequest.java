package com.quantum.api.kiwoom.dto.sector.chart;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.BaseChartRequest;
import com.quantum.api.kiwoom.dto.sector.common.BaseSectorRequest;
import com.quantum.api.kiwoom.dto.sector.common.SectorApiType;
import com.quantum.api.kiwoom.dto.sector.common.SectorCode;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

/**
 * 업종분봉조회요청 (ka20005) - 업종의 분봉 차트 데이터 조회
 * 
 * 특정 업종의 분봉 단위 시세 데이터를 조회합니다.
 * 1분, 3분, 5분, 10분, 30분, 60분 분봉을 지원합니다.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = false)
public class SectorMinuteChartRequest extends BaseSectorRequest {
    
    private static final String API_ID = "ka20005";
    
    /**
     * 업종코드 (필수)
     * 예: "001" (종합KOSPI), "101" (종합KOSDAQ)
     */
    @JsonProperty("FID_COND_MRKT_DIV_CODE")
    private String sectorCode;
    
    /**
     * 분봉구분 (필수)
     * 1: 1분봉, 3: 3분봉, 5: 5분봉, 10: 10분봉, 30: 30분봉, 60: 60분봉
     */
    @JsonProperty("FID_INPUT_HOUR_1")
    private Integer minuteType;
    
    /**
     * 조회 시작일자 (YYYYMMDD)
     * 생략 시 현재일자
     */
    @JsonProperty("FID_INPUT_DATE_1")
    private String fromDate;
    
    /**
     * 조회 시작시간 (HHMMSS)
     * 생략 시 장 시작시간
     */
    @JsonProperty("FID_INPUT_HOUR_2")
    private String fromTime;
    
    /**
     * 조회 종료일자 (YYYYMMDD)  
     * 생략 시 현재일자
     */
    @JsonProperty("FID_INPUT_DATE_2")
    private String toDate;
    
    /**
     * 조회 종료시간 (HHMMSS)
     * 생략 시 장 종료시간
     */
    @JsonProperty("FID_INPUT_HOUR_3")
    private String toTime;
    
    /**
     * 수정주가반영구분
     * 0: 수정주가 미반영, 1: 수정주가 반영 (기본값: 1)
     */
    @JsonProperty("FID_ORG_ADJ_PRC")
    private String adjustedPriceFlag;
    
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
        
        if (minuteType == null) {
            throw new IllegalArgumentException("분봉구분은 필수입니다.");
        }
        
        // 분봉구분 유효성 검증 (1, 3, 5, 10, 30, 60분만 지원)
        if (!isValidMinuteType(minuteType)) {
            throw new IllegalArgumentException("지원하지 않는 분봉구분입니다. 지원: 1, 3, 5, 10, 30, 60분");
        }
        
        // 날짜 형식 검증
        if (fromDate != null && !fromDate.matches("\\d{8}")) {
            throw new IllegalArgumentException("조회 시작일자는 YYYYMMDD 형식이어야 합니다.");
        }
        
        if (toDate != null && !toDate.matches("\\d{8}")) {
            throw new IllegalArgumentException("조회 종료일자는 YYYYMMDD 형식이어야 합니다.");
        }
        
        // 시간 형식 검증
        if (fromTime != null && !fromTime.matches("\\d{6}")) {
            throw new IllegalArgumentException("조회 시작시간은 HHMMSS 형식이어야 합니다.");
        }
        
        if (toTime != null && !toTime.matches("\\d{6}")) {
            throw new IllegalArgumentException("조회 종료시간은 HHMMSS 형식이어야 합니다.");
        }
        
        // 기본값 설정
        if (adjustedPriceFlag == null) {
            adjustedPriceFlag = "1"; // 수정주가 반영
        }
    }
    
    /**
     * 지원하는 분봉구분인지 확인
     */
    private boolean isValidMinuteType(Integer minuteType) {
        return minuteType == 1 || minuteType == 3 || minuteType == 5 || 
               minuteType == 10 || minuteType == 30 || minuteType == 60;
    }
    
    /**
     * 편의 메서드: 업종코드 설정
     */
    public static SectorMinuteChartRequestBuilder withSectorCode(String sectorCode) {
        return builder().sectorCode(sectorCode);
    }
    
    /**
     * 편의 메서드: 1분봉 차트 요청
     */
    public static SectorMinuteChartRequestBuilder oneMinuteChart(String sectorCode) {
        return builder()
                .sectorCode(sectorCode)
                .minuteType(1);
    }
    
    /**
     * 편의 메서드: 5분봉 차트 요청  
     */
    public static SectorMinuteChartRequestBuilder fiveMinuteChart(String sectorCode) {
        return builder()
                .sectorCode(sectorCode)
                .minuteType(5);
    }
    
    /**
     * 편의 메서드: 30분봉 차트 요청
     */
    public static SectorMinuteChartRequestBuilder thirtyMinuteChart(String sectorCode) {
        return builder()
                .sectorCode(sectorCode)
                .minuteType(30);
    }
    
    /**
     * 편의 메서드: 60분봉 차트 요청
     */
    public static SectorMinuteChartRequestBuilder hourlyChart(String sectorCode) {
        return builder()
                .sectorCode(sectorCode)
                .minuteType(60);
    }
}