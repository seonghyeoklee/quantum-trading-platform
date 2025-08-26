package com.quantum.trading.platform.shared.value;

/**
 * 종목 코드 Value Object (Record 타입)
 * 
 * 한국 주식의 6자리 종목 코드 (예: 005930 - 삼성전자)
 */
public record Symbol(String value) {
    
    public Symbol {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("Symbol cannot be null or empty");
        }
        
        value = value.trim();
        if (!isValidKoreanStockCode(value)) {
            throw new IllegalArgumentException("Invalid Korean stock symbol: " + value);
        }
    }
    
    public static Symbol of(String value) {
        return new Symbol(value);
    }
    
    /**
     * 한국 주식 종목 코드 검증
     * - 6자리 숫자
     * - A로 시작하는 경우는 특별주 (예: A005930)
     */
    private static boolean isValidKoreanStockCode(String code) {
        if (code.length() == 6 && code.matches("\\d{6}")) {
            return true;
        }
        
        if (code.length() == 7 && code.matches("A\\d{6}")) {
            return true;
        }
        
        return false;
    }
    
    /**
     * 종목 코드가 특별주인지 확인
     */
    public boolean isPreferredStock() {
        return value.startsWith("A");
    }
    
    /**
     * 기본 종목 코드 반환 (A 제거)
     */
    public String getBaseCode() {
        return isPreferredStock() ? value.substring(1) : value;
    }
    
    @Override
    public String toString() {
        return value;
    }
}