package com.quantum.trading.platform.shared.value;

import lombok.Value;

/**
 * 종목 코드 Value Object
 * 
 * 한국 주식의 6자리 종목 코드 (예: 005930 - 삼성전자)
 */
@Value
public class Symbol {
    String value;
    
    private Symbol(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("Symbol cannot be null or empty");
        }
        
        String trimmed = value.trim();
        if (!isValidKoreanStockCode(trimmed)) {
            throw new IllegalArgumentException("Invalid Korean stock symbol: " + trimmed);
        }
        
        this.value = trimmed;
    }
    
    public static Symbol of(String value) {
        return new Symbol(value);
    }
    
    /**
     * 한국 주식 종목 코드 검증
     * - 6자리 숫자
     * - A로 시작하는 경우는 특별주 (예: A005930)
     */
    private boolean isValidKoreanStockCode(String code) {
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