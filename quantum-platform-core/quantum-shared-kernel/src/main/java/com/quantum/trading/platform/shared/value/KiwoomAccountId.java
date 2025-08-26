package com.quantum.trading.platform.shared.value;

/**
 * 키움증권 계좌번호 Value Object
 * 
 * 키움증권 계좌번호는 일반적으로 8자리 숫자로 구성됨
 * 예: 12345678, 87654321
 */
public record KiwoomAccountId(String value) {

    public KiwoomAccountId {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("KiwoomAccountId cannot be null or empty");
        }
        
        String cleanValue = value.trim();
        
        // 계좌번호 형식 검증 (8자리 숫자)
        if (!cleanValue.matches("^\\d{8}$")) {
            throw new IllegalArgumentException("KiwoomAccountId must be 8 digits: " + cleanValue);
        }
        
        value = cleanValue;
    }

    public static KiwoomAccountId of(String value) {
        return new KiwoomAccountId(value);
    }
    
    public static KiwoomAccountId generate() {
        // 개발용 임시 계좌번호 생성 (실제로는 키움에서 발급받음)
        long timestamp = System.currentTimeMillis();
        String accountNumber = String.format("%08d", timestamp % 100000000);
        return new KiwoomAccountId(accountNumber);
    }
    
    @Override
    public String toString() {
        return value;
    }
}