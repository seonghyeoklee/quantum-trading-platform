package com.quantum.api.kiwoom.dto.chart.analysis;

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
 * 키움증권 거래원매물대분석요청 (ka10043) DTO
 * POST /api/dostk/stkinfo
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "거래원매물대분석요청 (ka10043)")
public class OrderBookAnalysisRequest extends BaseChartRequest {
    
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
     * 수정주가구분 (필수, 0 or 1)
     */
    @JsonProperty("upd_stkpc_tp")
    @Schema(description = "수정주가구분", example = "1", required = true, allowableValues = {"0", "1"})
    @Builder.Default
    private String updStkpcTp = "1";
    
    @Override
    public ChartApiType getApiType() {
        return ChartApiType.STOCK_INFO; // /api/dostk/stkinfo 사용
    }
    
    @Override
    public String getApiId() {
        return "ka10043";
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
    }
    
    /**
     * 기본 생성자 (Jackson 직렬화용)
     */
    public OrderBookAnalysisRequest() {
        super();
    }
    
    /**
     * 편의 생성자 - 종목코드와 기준일자로 생성
     */
    public static OrderBookAnalysisRequest of(String stockCode, String baseDate) {
        return OrderBookAnalysisRequest.builder()
                .stockCode(stockCode)
                .baseDate(baseDate)
                .updStkpcTp("1")
                .build();
    }
    
    /**
     * 편의 생성자 - 종목코드와 LocalDate로 생성
     */
    public static OrderBookAnalysisRequest of(String stockCode, LocalDate baseDate) {
        return of(stockCode, baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd")));
    }
    
    /**
     * 오늘 기준으로 생성
     */
    public static OrderBookAnalysisRequest ofToday(String stockCode) {
        return of(stockCode, LocalDate.now());
    }
}
