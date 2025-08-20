package com.quantum.api.kiwoom.dto.chart.investor;

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
 * 키움증권 종목별투자자기관별차트요청 (ka10060) DTO
 * POST /api/dostk/chart
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "종목별투자자기관별차트요청 (ka10060)")
public class InvestorAnalysisRequest extends BaseChartRequest {
    
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
     * 조회기간 구분
     * D: 일별, W: 주별, M: 월별
     */
    @JsonProperty("period_tp")
    @Schema(description = "조회기간 구분", example = "D", allowableValues = {"D", "W", "M"})
    @Builder.Default
    private String periodType = "D";
    
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
        return "ka10060";
    }
    
    @Override
    public void validate() {
        super.validate();
        
        if (stockCode == null || stockCode.trim().isEmpty()) {
            throw new IllegalArgumentException("종목코드는 필수입니다");
        }
        
        if (baseDate == null || baseDate.length() != 8) {
            throw new IllegalArgumentException("기준일자는 YYYYMMDD 형식이어야 합니다");
        }
        
        try {
            LocalDate.parse(baseDate, DateTimeFormatter.ofPattern("yyyyMMdd"));
        } catch (Exception e) {
            throw new IllegalArgumentException("기준일자 형식이 올바르지 않습니다: " + baseDate);
        }
        
        if (periodType == null || !isValidPeriodType(periodType)) {
            throw new IllegalArgumentException("유효하지 않은 조회기간 구분입니다: " + periodType);
        }
    }
    
    /**
     * 기본 생성자 (Jackson 직렬화용)
     */
    public InvestorAnalysisRequest() {
        super();
    }
    
    /**
     * 편의 생성자 - 종목코드, 기준일자, 조회기간으로 생성
     */
    public static InvestorAnalysisRequest of(String stockCode, String baseDate, String periodType) {
        return InvestorAnalysisRequest.builder()
                .stockCode(stockCode)
                .baseDate(baseDate)
                .periodType(periodType)
                .updStkpcTp("1")
                .build();
    }
    
    /**
     * 편의 생성자 - 종목코드와 기준일자로 생성 (일별 기본)
     */
    public static InvestorAnalysisRequest of(String stockCode, String baseDate) {
        return of(stockCode, baseDate, "D");
    }
    
    /**
     * 편의 생성자 - 종목코드와 LocalDate로 생성
     */
    public static InvestorAnalysisRequest of(String stockCode, LocalDate baseDate, String periodType) {
        return of(stockCode, baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd")), periodType);
    }
    
    /**
     * 편의 생성자 - 종목코드와 LocalDate로 생성 (일별 기본)
     */
    public static InvestorAnalysisRequest of(String stockCode, LocalDate baseDate) {
        return of(stockCode, baseDate, "D");
    }
    
    /**
     * 오늘 기준으로 생성
     */
    public static InvestorAnalysisRequest ofToday(String stockCode) {
        return of(stockCode, LocalDate.now());
    }
    
    /**
     * 오늘 기준으로 생성 (조회기간 지정)
     */
    public static InvestorAnalysisRequest ofToday(String stockCode, String periodType) {
        return of(stockCode, LocalDate.now(), periodType);
    }
    
    /**
     * 일별 투자자 분석 요청 생성
     */
    public static InvestorAnalysisRequest ofDaily(String stockCode, String baseDate) {
        return of(stockCode, baseDate, "D");
    }
    
    /**
     * 주별 투자자 분석 요청 생성
     */
    public static InvestorAnalysisRequest ofWeekly(String stockCode, String baseDate) {
        return of(stockCode, baseDate, "W");
    }
    
    /**
     * 월별 투자자 분석 요청 생성
     */
    public static InvestorAnalysisRequest ofMonthly(String stockCode, String baseDate) {
        return of(stockCode, baseDate, "M");
    }
    
    /**
     * 조회기간 구분 유효성 검증
     */
    private boolean isValidPeriodType(String periodType) {
        return "D".equals(periodType) || "W".equals(periodType) || "M".equals(periodType);
    }
    
    /**
     * 조회기간 구분별 한글 표시명
     */
    public String getPeriodDisplayName() {
        switch (periodType) {
            case "D": return "일별";
            case "W": return "주별";
            case "M": return "월별";
            default: return periodType;
        }
    }
    
    /**
     * 일별 조회 여부
     */
    public boolean isDaily() {
        return "D".equals(periodType);
    }
    
    /**
     * 주별 조회 여부
     */
    public boolean isWeekly() {
        return "W".equals(periodType);
    }
    
    /**
     * 월별 조회 여부
     */
    public boolean isMonthly() {
        return "M".equals(periodType);
    }
}
