package com.quantum.api.kiwoom.dto.chart.timeseries;

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
 * 키움증권 주식분봉차트조회요청 (ka10080) DTO
 * POST /api/dostk/chart
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "주식분봉차트조회요청 (ka10080)")
public class MinuteChartRequest extends BaseChartRequest {
    
    /**
     * 종목코드 (필수)
     */
    @JsonProperty("stk_cd")
    @Schema(description = "종목코드", example = "005930", required = true)
    private String stockCode;
    
    /**
     * 기준일자 (필수, YYYYMMDD)
     */
    @JsonProperty("base_dt")
    @Schema(description = "기준일자", example = "20241108", required = true, pattern = "yyyyMMdd")
    private String baseDate;
    
    /**
     * 분 구분 (필수)
     * 1: 1분, 3: 3분, 5: 5분, 10: 10분, 15: 15분, 30: 30분, 60: 60분
     */
    @JsonProperty("tic_scope")
    @Schema(description = "분 구분", example = "5", required = true, 
            allowableValues = {"1", "3", "5", "10", "15", "30", "60"})
    @Builder.Default
    private String ticScope = "5";
    
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
        return "ka10080";
    }
    
    @Override
    public void validate() {
        super.validate();
        
        if (stockCode == null || stockCode.trim().isEmpty()) {
            throw new IllegalArgumentException("종목코드는 필수입니다");
        }
        
        // baseDate가 빈 문자열인 경우 오늘 날짜로 설정
        if (baseDate == null || baseDate.trim().isEmpty()) {
            this.baseDate = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        }
        
        if (baseDate.length() != 8) {
            throw new IllegalArgumentException("기준일자는 YYYYMMDD 형식이어야 합니다");
        }
        
        try {
            LocalDate.parse(baseDate, DateTimeFormatter.ofPattern("yyyyMMdd"));
        } catch (Exception e) {
            throw new IllegalArgumentException("기준일자 형식이 올바르지 않습니다: " + baseDate);
        }
        
        if (ticScope == null || !isValidTicScope(ticScope)) {
            throw new IllegalArgumentException("유효하지 않은 분 구분입니다: " + ticScope);
        }
    }
    
    /**
     * 기본 생성자 (Jackson 직렬화용)
     */
    public MinuteChartRequest() {
        super();
    }
    
    /**
     * 편의 생성자 - 종목코드, 기준일자, 분 구분으로 생성
     */
    public static MinuteChartRequest of(String stockCode, String baseDate, String ticScope) {
        return MinuteChartRequest.builder()
                .stockCode(stockCode)
                .baseDate(baseDate)
                .ticScope(ticScope)
                .updStkpcTp("1")
                .build();
    }
    
    /**
     * 편의 생성자 - 종목코드와 LocalDate로 생성 (5분봉 기본)
     */
    public static MinuteChartRequest of(String stockCode, LocalDate baseDate) {
        return of(stockCode, baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd")), "5");
    }
    
    /**
     * 편의 생성자 - 종목코드와 LocalDate, 분 구분으로 생성
     */
    public static MinuteChartRequest of(String stockCode, LocalDate baseDate, String ticScope) {
        return of(stockCode, baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd")), ticScope);
    }
    
    /**
     * 오늘 기준으로 생성 (5분봉 기본)
     */
    public static MinuteChartRequest ofToday(String stockCode) {
        return of(stockCode, LocalDate.now(), "5");
    }
    
    /**
     * 오늘 기준으로 생성 (분 구분 지정)
     */
    public static MinuteChartRequest ofToday(String stockCode, String ticScope) {
        return of(stockCode, LocalDate.now(), ticScope);
    }
    
    /**
     * 분 구분 유효성 검증
     */
    private boolean isValidTicScope(String ticScope) {
        return "1".equals(ticScope) || "3".equals(ticScope) || "5".equals(ticScope) || 
               "10".equals(ticScope) || "15".equals(ticScope) || "30".equals(ticScope) || 
               "60".equals(ticScope);
    }
    
    /**
     * 분 구분을 분 단위로 변환
     */
    public int getTicScopeAsMinutes() {
        return Integer.parseInt(ticScope);
    }
    
    /**
     * 분 구분별 한글 표시명
     */
    public String getTicScopeDisplayName() {
        switch (ticScope) {
            case "1": return "1분";
            case "3": return "3분";
            case "5": return "5분";
            case "10": return "10분";
            case "15": return "15분";
            case "30": return "30분";
            case "60": return "60분";
            default: return ticScope + "분";
        }
    }
}