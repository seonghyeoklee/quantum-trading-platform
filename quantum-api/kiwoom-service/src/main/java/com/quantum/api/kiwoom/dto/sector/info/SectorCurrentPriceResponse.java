package com.quantum.api.kiwoom.dto.sector.info;

import com.quantum.api.kiwoom.dto.chart.common.BaseChartResponse;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

/**
 * 업종현재가요청 응답 DTO (ka20001)
 * 업종 현재가 정보 및 관련 종목 정보
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper=false)
@Schema(description = "업종현재가요청 응답 (ka20001)")
public class SectorCurrentPriceResponse extends BaseChartResponse {

    @Schema(description = "업종 정보")
    private SectorInfo sectorInfo;

    @Schema(description = "관련 종목 목록 (상위 또는 하위 종목)")
    private List<RelatedStock> relatedStocks;

    /**
     * 업종 정보 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "업종 정보")
    public static class SectorInfo {
        
        @Schema(description = "업종코드", example = "001")
        private String sectorCode;
        
        @Schema(description = "업종명", example = "종합(KOSPI)")
        private String sectorName;
        
        @Schema(description = "현재지수", example = "2450.75")
        private BigDecimal currentIndex;
        
        @Schema(description = "전일대비", example = "15.25")
        private BigDecimal changeAmount;
        
        @Schema(description = "등락률", example = "0.63")
        private BigDecimal changeRate;
        
        @Schema(description = "시가", example = "2435.50")
        private BigDecimal openIndex;
        
        @Schema(description = "고가", example = "2455.25")
        private BigDecimal highIndex;
        
        @Schema(description = "저가", example = "2430.75")
        private BigDecimal lowIndex;
        
        @Schema(description = "거래량", example = "524789000")
        private Long totalVolume;
        
        @Schema(description = "거래대금 (백만원)", example = "8745632")
        private Long totalValue;
        
        @Schema(description = "시가총액 (억원)", example = "1456789")
        private Long marketCap;
        
        @Schema(description = "상장종목수", example = "950")
        private Integer listedStockCount;
        
        @Schema(description = "상승종목수", example = "425")
        private Integer risingStockCount;
        
        @Schema(description = "하락종목수", example = "380")
        private Integer fallingStockCount;
        
        @Schema(description = "보합종목수", example = "145")
        private Integer unchangedStockCount;
    }
    
    /**
     * 관련 종목 정보 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "관련 종목 정보")
    public static class RelatedStock {
        
        @Schema(description = "종목코드", example = "005930")
        private String stockCode;
        
        @Schema(description = "종목명", example = "삼성전자")
        private String stockName;
        
        @Schema(description = "현재가", example = "74500")
        private BigDecimal currentPrice;
        
        @Schema(description = "전일대비", example = "1500")
        private BigDecimal changeAmount;
        
        @Schema(description = "등락률", example = "2.05")
        private BigDecimal changeRate;
        
        @Schema(description = "거래량", example = "25847592")
        private Long volume;
        
        @Schema(description = "거래대금 (백만원)", example = "1924567")
        private Long tradingValue;
        
        @Schema(description = "시가총액 비중 (%)", example = "25.8")
        private BigDecimal marketCapWeight;
        
        @Schema(description = "52주 최고가", example = "89000")
        private BigDecimal week52High;
        
        @Schema(description = "52주 최저가", example = "55300")
        private BigDecimal week52Low;
        
        @Schema(description = "PER", example = "12.5")
        private BigDecimal per;
        
        @Schema(description = "PBR", example = "1.2")
        private BigDecimal pbr;
    }
}