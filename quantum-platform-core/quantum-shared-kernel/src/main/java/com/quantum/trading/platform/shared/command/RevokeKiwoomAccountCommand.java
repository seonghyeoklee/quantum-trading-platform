package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;

/**
 * 사용자의 키움증권 계좌 할당을 취소하는 Command
 * 
 * - userId: 대상 사용자 ID
 * - reason: 취소 사유 (선택적)
 */
public record RevokeKiwoomAccountCommand(
    UserId userId,
    String reason
) {
    public RevokeKiwoomAccountCommand {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
    }
    
    public void validate() {
        // Additional business validation logic
        // Reason is optional, so no validation needed for it
    }
}