package com.quantum.api.kiwoom.dto.chart.investor;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.api.kiwoom.dto.chart.common.BaseChartResponse;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;

import java.util.List;

/**
 * 키움증권 종목별투자자기관별차트응답 (ka10060) DTO
 */
@Data
@EqualsAndHashCode(callSuper = true)
@SuperBuilder
@Schema(description = "종목별투자자기관별차트응답 (ka10060)")
public class InvestorAnalysisResponse extends BaseChartResponse {
    
    /**
     * 종목코드
     */
    @JsonProperty("stk_cd")
    @Schema(description = "종목코드", example = "005930")
    private String stockCode;
    
    /**
     * 종목명
     */
    @JsonProperty("stk_nm")
    @Schema(description = "종목명", example = "삼성전자")
    private String stockName;
    
    /**
     * 기준일자
     */
    @JsonProperty("base_dt")
    @Schema(description = "기준일자", example = "20241108")
    private String baseDate;
    
    /**
     * 조회기간 구분
     */
    @JsonProperty("period_tp")
    @Schema(description = "조회기간 구분", example = "D")
    private String periodType;
    
    /**
     * 투자자별 거래 데이터 리스트
     */
    @JsonProperty("output")
    @Schema(description = "투자자별 거래 데이터")
    @Builder.Default
    private List<InvestorAnalysisData> investorData = List.of();
    
    /**
     * 기본 생성자
     */
    public InvestorAnalysisResponse() {
        super();
    }
    
    /**
     * 데이터 없음 여부 확인
     */
    public boolean hasInvestorData() {
        return investorData != null && !investorData.isEmpty();
    }
    
    /**
     * 데이터 개수 반환
     */
    public int getInvestorDataCount() {
        return investorData != null ? investorData.size() : 0;
    }
    
    /**
     * 전체 순매수 합계
     */
    public long getTotalNetBuyQuantity() {
        return investorData.stream()
                .mapToLong(InvestorAnalysisData::getNetBuyQuantityAsLong)
                .sum();
    }
    
    /**
     * 전체 거래대금 합계
     */
    public long getTotalTradeAmount() {
        return investorData.stream()
                .mapToLong(InvestorAnalysisData::getTradeAmountAsLong)
                .sum();
    }
    
    /**
     * 주요 투자자 데이터 반환 (개인, 기관, 외국인)
     */
    public List<InvestorAnalysisData> getMajorInvestorData() {
        if (investorData == null || investorData.isEmpty()) {
            return List.of();
        }
        
        return investorData.stream()
                .filter(InvestorAnalysisData::isMajorInvestor)
                .toList();
    }
    
    /**
     * 순매수상위 N개 투자자 데이터 반환
     */
    public List<InvestorAnalysisData> getTopNetBuyInvestors(int limit) {
        if (investorData == null || investorData.isEmpty()) {
            return List.of();
        }
        
        return investorData.stream()
                .sorted((a, b) -> Long.compare(b.getNetBuyQuantityAsLong(), a.getNetBuyQuantityAsLong()))
                .limit(Math.min(limit, investorData.size()))
                .toList();
    }
    
    /**
     * 순매도상위 N개 투자자 데이터 반환
     */
    public List<InvestorAnalysisData> getTopNetSellInvestors(int limit) {
        if (investorData == null || investorData.isEmpty()) {
            return List.of();
        }
        
        return investorData.stream()
                .sorted((a, b) -> Long.compare(a.getNetBuyQuantityAsLong(), b.getNetBuyQuantityAsLong()))
                .limit(Math.min(limit, investorData.size()))
                .toList();
    }
    
    /**
     * 조회기간별 표시명
     */
    public String getPeriodDisplayName() {
        if (periodType == null) return "";
        switch (periodType) {
            case "D": return "일별";
            case "W": return "주별";
            case "M": return "월별";
            default: return periodType;
        }
    }
}
