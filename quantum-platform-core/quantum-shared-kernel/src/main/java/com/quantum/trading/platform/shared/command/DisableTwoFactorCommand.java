package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

/**
 * 2FA 비활성화 Command
 * 
 * 2FA 설정을 비활성화하는 명령
 */
public record DisableTwoFactorCommand(
    @TargetAggregateIdentifier
    UserId userId,
    String reason
) {
    
    public static DisableTwoFactorCommand of(UserId userId, String reason) {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        
        return new DisableTwoFactorCommand(userId, reason);
    }
    
    /**
     * Command 검증
     */
    public void validate() {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
    }
}