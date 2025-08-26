package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;

import java.time.Instant;
import java.util.Set;

/**
 * 2FA 활성화 Event
 * 
 * 사용자의 2FA가 성공적으로 활성화되었을 때 발행되는 이벤트
 */
public record TwoFactorEnabledEvent(
    UserId userId,
    String totpSecretKey,
    Set<String> backupCodeHashes,
    Instant enabledAt
) {
    
    public static TwoFactorEnabledEvent of(UserId userId, String totpSecretKey, Set<String> backupCodeHashes) {
        return new TwoFactorEnabledEvent(userId, totpSecretKey, backupCodeHashes, Instant.now());
    }
}