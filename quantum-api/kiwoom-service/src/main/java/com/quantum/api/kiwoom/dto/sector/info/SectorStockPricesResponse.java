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
 * 업종별주가요청 응답 DTO (ka20002)
 * 업종에 속한 종목들의 주가 정보
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper=false)
@Schema(description = "업종별주가요청 응답 (ka20002)")
public class SectorStockPricesResponse extends BaseChartResponse {

    @Schema(description = "업종 요약 정보")
    private SectorSummary sectorSummary;

    @Schema(description = "종목 목록")
    private List<StockPrice> stockPrices;

    @Schema(description = "페이징 정보")
    private PagingInfo pagingInfo;

    /**
     * 업종 요약 정보 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "업종 요약 정보")
    public static class SectorSummary {
        
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
        
        @Schema(description = "총 종목수", example = "950")
        private Integer totalStockCount;
        
        @Schema(description = "상승종목수", example = "425")
        private Integer risingStockCount;
        
        @Schema(description = "하락종목수", example = "380")
        private Integer fallingStockCount;
        
        @Schema(description = "보합종목수", example = "145")
        private Integer unchangedStockCount;
    }
    
    /**
     * 종목 주가 정보 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "종목 주가 정보")
    public static class StockPrice {
        
        @Schema(description = "순위", example = "1")
        private Integer rank;
        
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
        
        @Schema(description = "시가", example = "73000")
        private BigDecimal openPrice;
        
        @Schema(description = "고가", example = "75000")
        private BigDecimal highPrice;
        
        @Schema(description = "저가", example = "72500")
        private BigDecimal lowPrice;
        
        @Schema(description = "거래량", example = "25847592")
        private Long volume;
        
        @Schema(description = "거래대금 (백만원)", example = "1924567")
        private Long tradingValue;
        
        @Schema(description = "시가총액 (억원)", example = "445820")
        private Long marketCap;
        
        @Schema(description = "시가총액 비중 (%)", example = "25.8")
        private BigDecimal marketCapWeight;
        
        @Schema(description = "52주 최고가", example = "89000")
        private BigDecimal week52High;
        
        @Schema(description = "52주 최저가", example = "55300")
        private BigDecimal week52Low;
        
        @Schema(description = "상장주식수 (천주)", example = "5969783")
        private Long listedShares;
        
        @Schema(description = "PER", example = "12.5")
        private BigDecimal per;
        
        @Schema(description = "PBR", example = "1.2")
        private BigDecimal pbr;
        
        @Schema(description = "ROE", example = "9.8")
        private BigDecimal roe;
        
        @Schema(description = "배당수익률", example = "2.1")
        private BigDecimal dividendYield;
        
        @Schema(description = "베타값", example = "0.95")
        private BigDecimal beta;
        
        @Schema(description = "거래소구분 (1:KRX, 2:NXT, 3:통합)", example = "1")
        private String exchangeType;
        
        @Schema(description = "업종분류", example = "반도체")
        private String industryCategory;
    }
    
    /**
     * 페이징 정보 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "페이징 정보")
    public static class PagingInfo {
        
        @Schema(description = "현재 페이지", example = "1")
        private Integer currentPage;
        
        @Schema(description = "페이지 크기", example = "50")
        private Integer pageSize;
        
        @Schema(description = "총 데이터 수", example = "950")
        private Integer totalCount;
        
        @Schema(description = "총 페이지 수", example = "19")
        private Integer totalPages;
        
        @Schema(description = "다음 페이지 존재 여부", example = "true")
        private Boolean hasNext;
        
        @Schema(description = "이전 페이지 존재 여부", example = "false")
        private Boolean hasPrevious;
        
        @Schema(description = "다음 페이지 시작 인덱스", example = "51")
        private Integer nextStartIndex;
    }
}