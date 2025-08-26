package com.quantum.trading.platform.shared.value;

import lombok.Value;

/**
 * API 인증 정보 Value Object
 * 
 * 키움증권 API 접근을 위한 클라이언트 인증 정보
 * - clientId: 키움에서 발급한 클라이언트 ID
 * - clientSecret: 키움에서 발급한 클라이언트 시크릿
 */
@Value
public class ApiCredentials {
    String clientId;
    String clientSecret;

    public static ApiCredentials of(String clientId, String clientSecret) {
        if (clientId == null || clientId.trim().isEmpty()) {
            throw new IllegalArgumentException("Client ID cannot be null or empty");
        }
        
        if (clientSecret == null || clientSecret.trim().isEmpty()) {
            throw new IllegalArgumentException("Client Secret cannot be null or empty");
        }
        
        return new ApiCredentials(clientId.trim(), clientSecret.trim());
    }
    
    /**
     * 보안을 위해 toString에서 시크릿 마스킹
     */
    @Override
    public String toString() {
        return String.format("ApiCredentials{clientId='%s', clientSecret='%s***'}", 
                           clientId, 
                           clientSecret.substring(0, Math.min(3, clientSecret.length())));
    }
}