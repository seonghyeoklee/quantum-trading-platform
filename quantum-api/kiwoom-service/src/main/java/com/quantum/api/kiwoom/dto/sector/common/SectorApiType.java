package com.quantum.api.kiwoom.dto.sector.common;

/**
 * 업종 API 타입 enum
 * 키움증권 업종 관련 API의 엔드포인트 라우팅을 위한 타입 정의
 */
public enum SectorApiType {
    
    /**
     * 업종 정보 조회 API
     * /api/dostk/sect 엔드포인트 사용
     * - ka20001: 업종현재가요청
     * - ka20002: 업종별주가요청  
     * - ka20003: 전업종지수요청
     * - ka20009: 업종현재가일별요청
     */
    SECTOR_INFO("/api/dostk/sect"),
    
    /**
     * 업종 차트 조회 API
     * /api/dostk/chart 엔드포인트 사용
     * - ka20005: 업종분봉조회요청
     * - ka20006: 업종일봉조회요청
     * - ka20007: 업종주봉조회요청
     * - ka20008: 업종월봉조회요청
     */
    SECTOR_CHART("/api/dostk/chart");
    
    private final String endpoint;
    
    SectorApiType(String endpoint) {
        this.endpoint = endpoint;
    }
    
    public String getEndpoint() {
        return endpoint;
    }
    
    /**
     * API ID를 기반으로 적절한 SectorApiType 반환
     */
    public static SectorApiType fromApiId(String apiId) {
        if (apiId == null) {
            throw new IllegalArgumentException("API ID cannot be null");
        }
        
        switch (apiId) {
            case "ka20001":
            case "ka20002": 
            case "ka20003":
            case "ka20009":
                return SECTOR_INFO;
                
            case "ka20005":
            case "ka20006":
            case "ka20007": 
            case "ka20008":
                return SECTOR_CHART;
                
            default:
                throw new IllegalArgumentException("Unknown sector API ID: " + apiId);
        }
    }
}