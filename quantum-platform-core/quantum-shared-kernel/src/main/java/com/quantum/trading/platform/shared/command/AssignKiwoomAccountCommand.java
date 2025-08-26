package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.KiwoomAccountId;
import com.quantum.trading.platform.shared.value.ApiCredentials;

/**
 * 사용자에게 키움증권 계좌를 할당하는 Command
 * 
 * - userId: 할당받을 사용자 ID
 * - kiwoomAccountId: 할당할 키움증권 계좌번호
 * - apiCredentials: API 인증 정보 (client_id, client_secret)
 */
public record AssignKiwoomAccountCommand(
    UserId userId,
    KiwoomAccountId kiwoomAccountId,
    ApiCredentials apiCredentials
) {
    public AssignKiwoomAccountCommand {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        
        if (kiwoomAccountId == null) {
            throw new IllegalArgumentException("KiwoomAccountId cannot be null");
        }
        
        if (apiCredentials == null) {
            throw new IllegalArgumentException("ApiCredentials cannot be null");
        }
    }
    
    public void validate() {
        // Additional business validation logic
        if (apiCredentials.getClientId().trim().isEmpty()) {
            throw new IllegalArgumentException("Client ID cannot be empty");
        }
        
        if (apiCredentials.getClientSecret().trim().isEmpty()) {
            throw new IllegalArgumentException("Client Secret cannot be empty");
        }
    }
}