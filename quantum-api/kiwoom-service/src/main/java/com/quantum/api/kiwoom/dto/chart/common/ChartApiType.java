package com.quantum.api.kiwoom.dto.chart.common;

/**
 * 키움증권 차트 API 타입
 * URL 라우팅을 위한 분류
 */
public enum ChartApiType {
    
    /**
     * 차트 API - /api/dostk/chart
     * 대부분의 차트 API (7개)
     */
    CHART("/api/dostk/chart"),
    
    /**
     * 종목정보 API - /api/dostk/stkinfo  
     * 거래원매물대분석 (ka10043)만 사용
     */
    STOCK_INFO("/api/dostk/stkinfo");
    
    private final String endpoint;
    
    ChartApiType(String endpoint) {
        this.endpoint = endpoint;
    }
    
    /**
     * API 엔드포인트 URL 반환
     */
    public String getEndpoint() {
        return endpoint;
    }
}