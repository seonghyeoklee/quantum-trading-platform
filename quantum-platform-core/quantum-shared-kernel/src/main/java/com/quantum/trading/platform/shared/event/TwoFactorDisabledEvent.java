package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;

import java.time.Instant;

/**
 * 2FA 비활성화 Event
 * 
 * 사용자의 2FA가 비활성화되었을 때 발행되는 이벤트
 */
public record TwoFactorDisabledEvent(
    UserId userId,
    String reason,
    Instant disabledAt
) {
    
    public static TwoFactorDisabledEvent of(UserId userId, String reason) {
        return new TwoFactorDisabledEvent(userId, reason, Instant.now());
    }
}