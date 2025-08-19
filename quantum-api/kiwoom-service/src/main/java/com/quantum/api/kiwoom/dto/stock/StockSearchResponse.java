package com.quantum.api.kiwoom.dto.stock;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 종목 검색 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StockSearchResponse {
    private String symbol;              // 종목코드
    private String stockName;           // 종목명
    private String stockNameEng;        // 종목명(영문)
    private String marketType;          // 시장구분 (KOSPI/KOSDAQ/KONEX)
    private String industryName;        // 업종명
    private String listingDate;         // 상장일
}