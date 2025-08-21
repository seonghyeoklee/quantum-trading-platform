package com.quantum.api.kiwoom.dto.chart.sector;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.BaseChartRequest;
import com.quantum.api.kiwoom.dto.chart.common.ChartApiType;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 키움증권 업종틱차트조회요청 (ka20004) DTO
 * POST /api/dostk/chart
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "업종틱차트조회요청 (ka20004)")
public class SectorTickChartRequest extends BaseChartRequest {
    
    /**
     * 업종코드 (필수)
     * 예: "0001" - 코스피, "1001" - 코스닥
     */
    @JsonProperty("upjong_cd")
    @Schema(description = "업종코드", example = "0001", required = true)
    private String sectorCode;
    
    /**
     * 기준일자 (필수, YYYYMMDD)
     */
    @JsonProperty("base_dt")
    @Schema(description = "기준일자", example = "20241108", required = true, pattern = "yyyyMMdd")
    private String baseDate;
    
    /**
     * 수정주가구분 (필수, 0 or 1)
     */
    @JsonProperty("upd_stkpc_tp")
    @Schema(description = "수정주가구분", example = "1", required = true, allowableValues = {"0", "1"})
    @Builder.Default
    private String updStkpcTp = "1";
    
    @Override
    public ChartApiType getApiType() {
        return ChartApiType.CHART;
    }
    
    @Override
    public String getApiId() {
        return "ka20004";
    }
    
    @Override
    public void validate() {
        super.validate();
        
        if (sectorCode == null || sectorCode.trim().isEmpty()) {
            throw new IllegalArgumentException("업종코드는 필수입니다");
        }
        
        if (baseDate == null || baseDate.length() != 8) {
            throw new IllegalArgumentException("기준일자는 YYYYMMDD 형식이어야 합니다");
        }
        
        try {
            LocalDate.parse(baseDate, DateTimeFormatter.ofPattern("yyyyMMdd"));
        } catch (Exception e) {
            throw new IllegalArgumentException("기준일자 형식이 올바르지 않습니다: " + baseDate);
        }
    }
    
    /**
     * 기본 생성자 (Jackson 직렬화용)
     */
    public SectorTickChartRequest() {
        super();
    }
    
    /**
     * 편의 생성자 - 업종코드와 기준일자로 생성
     */
    public static SectorTickChartRequest of(String sectorCode, String baseDate) {
        return SectorTickChartRequest.builder()
                .sectorCode(sectorCode)
                .baseDate(baseDate)
                .updStkpcTp("1")
                .build();
    }
    
    /**
     * 편의 생성자 - 업종코드와 LocalDate로 생성
     */
    public static SectorTickChartRequest of(String sectorCode, LocalDate baseDate) {
        return of(sectorCode, baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd")));
    }
    
    /**
     * 오늘 기준으로 생성
     */
    public static SectorTickChartRequest ofToday(String sectorCode) {
        return of(sectorCode, LocalDate.now());
    }
    
    /**
     * 코스피 업종틱차트 생성
     */
    public static SectorTickChartRequest ofKospi(String baseDate) {
        return of("0001", baseDate);
    }
    
    /**
     * 코스닥 업종틱차트 생성
     */
    public static SectorTickChartRequest ofKosdaq(String baseDate) {
        return of("1001", baseDate);
    }
    
    /**
     * 오늘 기준 코스피 업종틱차트 생성
     */
    public static SectorTickChartRequest ofKospiToday() {
        return ofKospi(LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd")));
    }
    
    /**
     * 오늘 기준 코스닥 업종틱차트 생성
     */
    public static SectorTickChartRequest ofKosdaqToday() {
        return ofKosdaq(LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd")));
    }
    
    /**
     * 업종코드별 한글명 반환
     */
    public String getSectorDisplayName() {
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
    
    /**
     * 주요 업종코드인지 확인
     */
    public boolean isMajorSector() {
        return "0001".equals(sectorCode) || "1001".equals(sectorCode) || "2001".equals(sectorCode);
    }
}