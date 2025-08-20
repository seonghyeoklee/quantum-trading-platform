package com.quantum.api.kiwoom.dto.sector.common;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * 업종 API 요청 기본 클래스
 * 모든 업종 관련 API 요청의 공통 구조를 정의
 */
public abstract class BaseSectorRequest {
    
    /**
     * API 타입 반환 (SECTOR_INFO 또는 SECTOR_CHART)
     */
    public abstract SectorApiType getApiType();
    
    /**
     * API ID 반환 (ka20001, ka20002, ...)
     */
    public abstract String getApiId();
    
    /**
     * 요청 데이터 유효성 검증
     */
    public void validate() {
        String apiId = getApiId();
        if (apiId == null || apiId.trim().isEmpty()) {
            throw new IllegalArgumentException("API ID는 필수입니다");
        }
        
        if (!apiId.matches("ka20[0-9]{3}")) {
            throw new IllegalArgumentException("올바르지 않은 API ID 형식입니다: " + apiId);
        }
        
        SectorApiType expectedType = SectorApiType.fromApiId(apiId);
        if (getApiType() != expectedType) {
            throw new IllegalArgumentException(
                String.format("API ID %s는 %s 타입이어야 하지만 %s 타입으로 설정되었습니다", 
                    apiId, expectedType, getApiType()));
        }
    }
    
    /**
     * 업종 코드 유효성 검증
     */
    protected void validateSectorCode(String sectorCode) {
        if (sectorCode == null || sectorCode.trim().isEmpty()) {
            throw new IllegalArgumentException("업종코드는 필수입니다");
        }
        
        if (sectorCode.length() != 3) {
            throw new IllegalArgumentException("업종코드는 3자리여야 합니다: " + sectorCode);
        }
        
        try {
            SectorCode.fromCode(sectorCode);
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("유효하지 않은 업종코드입니다: " + sectorCode);
        }
    }
    
    /**
     * 시장 구분 유효성 검증
     */
    protected void validateMarketType(String marketType) {
        if (marketType == null || marketType.trim().isEmpty()) {
            throw new IllegalArgumentException("시장구분은 필수입니다");
        }
        
        if (!marketType.matches("[0-2]")) {
            throw new IllegalArgumentException("시장구분은 0(코스피), 1(코스닥), 2(코스피200) 중 하나여야 합니다: " + marketType);
        }
    }
    
    /**
     * 기준일자 유효성 검증 (YYYYMMDD)
     */
    protected void validateBaseDate(String baseDate) {
        if (baseDate == null || baseDate.length() != 8) {
            throw new IllegalArgumentException("기준일자는 YYYYMMDD 형식이어야 합니다");
        }
        
        if (!baseDate.matches("\\d{8}")) {
            throw new IllegalArgumentException("기준일자는 숫자 8자리여야 합니다: " + baseDate);
        }
        
        try {
            int year = Integer.parseInt(baseDate.substring(0, 4));
            int month = Integer.parseInt(baseDate.substring(4, 6));
            int day = Integer.parseInt(baseDate.substring(6, 8));
            
            if (year < 1900 || year > 2100) {
                throw new IllegalArgumentException("유효하지 않은 연도입니다: " + year);
            }
            if (month < 1 || month > 12) {
                throw new IllegalArgumentException("유효하지 않은 월입니다: " + month);
            }
            if (day < 1 || day > 31) {
                throw new IllegalArgumentException("유효하지 않은 일입니다: " + day);
            }
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("기준일자 형식이 올바르지 않습니다: " + baseDate);
        }
    }
}