package com.quantum.api.kiwoom.dto.sector.info;

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
 * 업종현재가일별요청 (ka20009) - 업종의 일별 상세 현재가 데이터 조회
 * 
 * 특정 업종의 일별 상세 시세 데이터를 조회합니다.
 * 업종지수, 거래량, 거래대금 등의 반복적인 일별 데이터를 제공합니다.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = false)
public class SectorDailyDetailRequest extends BaseSectorRequest {
    
    private static final String API_ID = "ka20009";
    
    /**
     * 업종코드 (필수)
     * 예: "001" (종합KOSPI), "101" (종합KOSDAQ)
     */
    @JsonProperty("FID_COND_MRKT_DIV_CODE")
    private String sectorCode;
    
    /**
     * 조회 시작일자 (YYYYMMDD) (필수)
     * 조회하고자 하는 시작일자
     */
    @JsonProperty("FID_INPUT_DATE_1")
    private String fromDate;
    
    /**
     * 조회 종료일자 (YYYYMMDD) (필수)  
     * 조회하고자 하는 종료일자
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
     * 연속조회키
     * 다음 페이지 조회를 위한 키 (첫 조회시에는 공백)
     */
    @JsonProperty("FID_COND_SCR_DIV_CODE")
    private String continuationKey;
    
    @Override
    public SectorApiType getApiType() {
        return SectorApiType.SECTOR_INFO;
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
    }
    
    /**
     * 편의 메서드: 업종코드 설정
     */
    public static SectorDailyDetailRequestBuilder withSectorCode(String sectorCode) {
        return builder().sectorCode(sectorCode);
    }
    
    /**
     * 편의 메서드: 기간 지정 일별 상세 요청
     */
    public static SectorDailyDetailRequestBuilder forPeriod(String sectorCode, String fromDate, String toDate) {
        return builder()
                .sectorCode(sectorCode)
                .fromDate(fromDate)
                .toDate(toDate);
    }
    
    /**
     * 편의 메서드: 연속조회 요청
     */
    public static SectorDailyDetailRequestBuilder withContinuation(String sectorCode, String fromDate, 
                                                                   String toDate, String continuationKey) {
        return builder()
                .sectorCode(sectorCode)
                .fromDate(fromDate)
                .toDate(toDate)
                .continuationKey(continuationKey);
    }
}