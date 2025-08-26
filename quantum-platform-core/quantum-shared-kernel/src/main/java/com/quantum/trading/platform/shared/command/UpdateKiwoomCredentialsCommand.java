package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.ApiCredentials;

/**
 * 사용자의 키움증권 API 인증 정보를 업데이트하는 Command
 * 
 * - userId: 대상 사용자 ID
 * - newApiCredentials: 새로운 API 인증 정보
 */
public record UpdateKiwoomCredentialsCommand(
    UserId userId,
    ApiCredentials newApiCredentials
) {
    public UpdateKiwoomCredentialsCommand {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        
        if (newApiCredentials == null) {
            throw new IllegalArgumentException("New API credentials cannot be null");
        }
    }
    
    public void validate() {
        // Additional business validation logic
        if (newApiCredentials.getClientId().trim().isEmpty()) {
            throw new IllegalArgumentException("New Client ID cannot be empty");
        }
        
        if (newApiCredentials.getClientSecret().trim().isEmpty()) {
            throw new IllegalArgumentException("New Client Secret cannot be empty");
        }
    }
}