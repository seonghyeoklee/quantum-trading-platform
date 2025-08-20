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
 * 전업종지수요청 응답 DTO (ka20003)
 * 전체 업종 지수의 현재가 정보
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper=false)
@Schema(description = "전업종지수요청 응답 (ka20003)")
public class AllSectorIndicesResponse extends BaseChartResponse {

    @Schema(description = "시장 요약 정보")
    private MarketSummary marketSummary;

    @Schema(description = "업종 지수 목록")
    private List<SectorIndex> sectorIndices;

    @Schema(description = "통계 정보")
    private StatisticsInfo statisticsInfo;

    /**
     * 시장 요약 정보 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "시장 요약 정보")
    public static class MarketSummary {
        
        @Schema(description = "시장구분명", example = "전체시장")
        private String marketName;
        
        @Schema(description = "시장 대표지수", example = "2450.75")
        private BigDecimal representativeIndex;
        
        @Schema(description = "시장 전일대비", example = "15.25")
        private BigDecimal marketChangeAmount;
        
        @Schema(description = "시장 등락률", example = "0.63")
        private BigDecimal marketChangeRate;
        
        @Schema(description = "총 업종수", example = "25")
        private Integer totalSectorCount;
        
        @Schema(description = "상승 업종수", example = "15")
        private Integer risingSectorCount;
        
        @Schema(description = "하락 업종수", example = "8")
        private Integer fallingSectorCount;
        
        @Schema(description = "보합 업종수", example = "2")
        private Integer unchangedSectorCount;
        
        @Schema(description = "시장 총 거래량", example = "1245678900")
        private Long totalVolume;
        
        @Schema(description = "시장 총 거래대금 (백만원)", example = "15678923")
        private Long totalValue;
    }
    
    /**
     * 업종 지수 정보 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "업종 지수 정보")
    public static class SectorIndex {
        
        @Schema(description = "순위", example = "1")
        private Integer rank;
        
        @Schema(description = "업종코드", example = "001")
        private String sectorCode;
        
        @Schema(description = "업종명", example = "종합(KOSPI)")
        private String sectorName;
        
        @Schema(description = "업종분류", example = "대분류")
        private String categoryName;
        
        @Schema(description = "현재지수", example = "2450.75")
        private BigDecimal currentIndex;
        
        @Schema(description = "전일대비", example = "15.25")
        private BigDecimal changeAmount;
        
        @Schema(description = "등락률", example = "0.63")
        private BigDecimal changeRate;
        
        @Schema(description = "시가지수", example = "2435.50")
        private BigDecimal openIndex;
        
        @Schema(description = "고가지수", example = "2455.25")
        private BigDecimal highIndex;
        
        @Schema(description = "저가지수", example = "2430.75")
        private BigDecimal lowIndex;
        
        @Schema(description = "거래량", example = "524789000")
        private Long volume;
        
        @Schema(description = "거래대금 (백만원)", example = "8745632")
        private Long tradingValue;
        
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
        
        @Schema(description = "52주 최고지수", example = "2650.25")
        private BigDecimal week52HighIndex;
        
        @Schema(description = "52주 최저지수", example = "2180.50")
        private BigDecimal week52LowIndex;
        
        @Schema(description = "연초대비 등락률", example = "8.5")
        private BigDecimal yearToDateChangeRate;
        
        @Schema(description = "월초대비 등락률", example = "2.1")
        private BigDecimal monthToDateChangeRate;
        
        @Schema(description = "주초대비 등락률", example = "0.8")
        private BigDecimal weekToDateChangeRate;
        
        @Schema(description = "기준지수 (100 기준)", example = "100.0")
        private BigDecimal baseIndex;
        
        @Schema(description = "시장구분 (0:코스피, 1:코스닥, 2:코스피200)", example = "0")
        private String marketType;
        
        @Schema(description = "지수가중치 (%)", example = "35.2")
        private BigDecimal indexWeight;
    }
    
    /**
     * 통계 정보 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "통계 정보")
    public static class StatisticsInfo {
        
        @Schema(description = "평균 등락률", example = "0.45")
        private BigDecimal averageChangeRate;
        
        @Schema(description = "최고 등락률", example = "3.25")
        private BigDecimal maxChangeRate;
        
        @Schema(description = "최저 등락률", example = "-2.15")
        private BigDecimal minChangeRate;
        
        @Schema(description = "거래량 가중평균지수", example = "2448.75")
        private BigDecimal volumeWeightedIndex;
        
        @Schema(description = "시가총액 가중평균지수", example = "2452.25")
        private BigDecimal marketCapWeightedIndex;
        
        @Schema(description = "상승 업종 비율 (%)", example = "60.0")
        private BigDecimal risingRatio;
        
        @Schema(description = "하락 업종 비율 (%)", example = "32.0")
        private BigDecimal fallingRatio;
        
        @Schema(description = "전체 업종 평균 거래량", example = "20991156")
        private Long averageVolume;
        
        @Schema(description = "전체 업종 평균 거래대금 (백만원)", example = "349865")
        private Long averageTradingValue;
        
        @Schema(description = "조회 시점", example = "20241120 153000")
        private String queryTimestamp;
    }
}