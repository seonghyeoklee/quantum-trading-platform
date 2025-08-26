package com.quantum.trading.platform.shared.value;

/**
 * 암호화된 값을 표현하는 Value Object
 * <p>
 * 민감한 정보를 암호화하여 저장할 때 사용 - encryptedData: AES-256으로 암호화된 데이터 - salt: 암호화에 사용된 솔트 값
 */
public record EncryptedValue(String encryptedData, String salt) {

    public static EncryptedValue of(String encryptedData, String salt) {
        if (encryptedData == null || encryptedData.trim().isEmpty()) {
            throw new IllegalArgumentException("Encrypted data cannot be null or empty");
        }

        if (salt == null || salt.trim().isEmpty()) {
            throw new IllegalArgumentException("Salt cannot be null or empty");
        }

        return new EncryptedValue(encryptedData.trim(), salt.trim());
    }

    /**
     * 보안을 위해 toString에서 암호화된 데이터 마스킹
     */
    @Override
    public String toString() {
        return String.format("EncryptedValue{encryptedData='%s***', salt='%s***'}",
                encryptedData.substring(0, Math.min(8, encryptedData.length())),
                salt.substring(0, Math.min(8, salt.length())));
    }
}
