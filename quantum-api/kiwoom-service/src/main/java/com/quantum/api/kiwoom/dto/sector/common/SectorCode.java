package com.quantum.api.kiwoom.dto.sector.common;

/**
 * 키움증권 업종 코드 enum
 * 업종별 코드와 한글명 매핑
 */
public enum SectorCode {
    
    // KOSPI 업종
    KOSPI_TOTAL("001", "종합(KOSPI)", MarketType.KOSPI),
    KOSPI_LARGE("002", "대형주", MarketType.KOSPI),
    KOSPI_MEDIUM("003", "중형주", MarketType.KOSPI),
    KOSPI_SMALL("004", "소형주", MarketType.KOSPI),
    
    // KOSDAQ 업종
    KOSDAQ_TOTAL("101", "종합(KOSDAQ)", MarketType.KOSDAQ),
    
    // 기타 지수
    KOSPI200("201", "KOSPI200", MarketType.KOSPI200),
    KOSTAR("302", "KOSTAR", MarketType.KOSDAQ),
    KRX100("701", "KRX100", MarketType.KOSPI);
    
    private final String code;
    private final String name;
    private final MarketType marketType;
    
    SectorCode(String code, String name, MarketType marketType) {
        this.code = code;
        this.name = name;
        this.marketType = marketType;
    }
    
    public String getCode() {
        return code;
    }
    
    public String getName() {
        return name;
    }
    
    public MarketType getMarketType() {
        return marketType;
    }
    
    /**
     * 코드로 SectorCode 찾기
     */
    public static SectorCode fromCode(String code) {
        if (code == null || code.trim().isEmpty()) {
            throw new IllegalArgumentException("Sector code cannot be null or empty");
        }
        
        for (SectorCode sectorCode : values()) {
            if (sectorCode.code.equals(code.trim())) {
                return sectorCode;
            }
        }
        
        throw new IllegalArgumentException("Unknown sector code: " + code);
    }
    
    /**
     * 시장 타입별 업종 코드 목록 조회
     */
    public static SectorCode[] getBySectorType(MarketType marketType) {
        return java.util.Arrays.stream(values())
                .filter(sector -> sector.marketType == marketType)
                .toArray(SectorCode[]::new);
    }
    
    /**
     * 주요 업종 여부 (KOSPI 종합, KOSDAQ 종합, KOSPI200)
     */
    public boolean isMajorSector() {
        return this == KOSPI_TOTAL || this == KOSDAQ_TOTAL || this == KOSPI200;
    }
    
    /**
     * 시장 구분
     */
    public enum MarketType {
        KOSPI("0", "코스피"),
        KOSDAQ("1", "코스닥"), 
        KOSPI200("2", "코스피200");
        
        private final String code;
        private final String name;
        
        MarketType(String code, String name) {
            this.code = code;
            this.name = name;
        }
        
        public String getCode() {
            return code;
        }
        
        public String getName() {
            return name;
        }
        
        public static MarketType fromCode(String code) {
            for (MarketType type : values()) {
                if (type.code.equals(code)) {
                    return type;
                }
            }
            throw new IllegalArgumentException("Unknown market type code: " + code);
        }
    }
}