package com.quantum.stock.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 종목 검색 결과 DTO
 *
 * 종목 검색 API 응답을 위한 데이터 전송 객체
 * 프론트엔드에서 자동완성 UI에 필요한 정보만 포함
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StockSearchResult {

    /**
     * 6자리 종목코드 (예: 005930)
     */
    private String stockCode;

    /**
     * 회사명 (예: 삼성전자)
     */
    private String companyName;

    /**
     * 영문 회사명 (예: Samsung Electronics Co., Ltd.)
     */
    private String companyNameEn;

    /**
     * 시장구분 (KOSPI/KOSDAQ)
     */
    private String marketType;

    /**
     * 업종 (예: 전기전자, 화학, 의약품 등)
     */
    private String sector;

    /**
     * 표시명 (종목코드 + 회사명)
     * 예: "005930 삼성전자"
     */
    private String displayName;

    /**
     * 전체 표시명 (종목코드 + 회사명 + 영문명)
     * 예: "005930 삼성전자 Samsung Electronics Co., Ltd."
     */
    private String fullDisplayName;

    /**
     * 상장여부 (true: 상장, false: 폐지)
     */
    private Boolean isActive;

    /**
     * 검색 매치 타입 (정확일치/부분일치/유사일치)
     * 프론트엔드에서 하이라이팅용으로 사용
     */
    private String matchType;

    /**
     * 검색 관련도 점수 (0-100)
     * 프론트엔드에서 정렬 우선순위 판단용
     */
    private Integer relevanceScore;

    /**
     * 자동완성 표시용 라벨 생성
     * HTML 태그 포함 가능 (하이라이팅용)
     */
    public String getAutocompleteLabel() {
        return this.displayName;
    }

    /**
     * 자동완성 값 생성 (실제 선택시 사용할 값)
     */
    public String getAutocompleteValue() {
        return this.stockCode;
    }

    /**
     * 검색 결과 타입 판별
     */
    public String getResultType() {
        if (stockCode != null && stockCode.length() == 6 && stockCode.matches("\\d{6}")) {
            return "stock_code";
        } else if (companyName != null && !companyName.isEmpty()) {
            return "company_name";
        } else {
            return "unknown";
        }
    }

    /**
     * 시장 아이콘 CSS 클래스
     */
    public String getMarketIconClass() {
        if ("KOSPI".equals(marketType)) {
            return "market-kospi";
        } else if ("KOSDAQ".equals(marketType)) {
            return "market-kosdaq";
        } else {
            return "market-unknown";
        }
    }

    /**
     * 업종 색상 CSS 클래스
     */
    public String getSectorColorClass() {
        if (sector == null || sector.isEmpty()) {
            return "sector-default";
        }

        switch (sector) {
            case "전기전자":
                return "sector-tech";
            case "화학":
                return "sector-chemical";
            case "의약품":
                return "sector-pharma";
            case "자동차부품":
                return "sector-automotive";
            case "은행":
                return "sector-finance";
            case "서비스업":
                return "sector-service";
            case "철강금속":
                return "sector-steel";
            case "통신업":
                return "sector-telecom";
            case "건설업":
                return "sector-construction";
            case "기타금융":
                return "sector-finance-other";
            case "전기가스업":
                return "sector-utility";
            case "보험":
                return "sector-insurance";
            case "IT":
                return "sector-it";
            default:
                return "sector-default";
        }
    }

    /**
     * JSON 직렬화를 위한 간소화된 정보
     */
    public StockSearchResult forJson() {
        return StockSearchResult.builder()
                .stockCode(this.stockCode)
                .companyName(this.companyName)
                .companyNameEn(this.companyNameEn)
                .marketType(this.marketType)
                .sector(this.sector)
                .displayName(this.displayName)
                .isActive(this.isActive)
                .build();
    }
}