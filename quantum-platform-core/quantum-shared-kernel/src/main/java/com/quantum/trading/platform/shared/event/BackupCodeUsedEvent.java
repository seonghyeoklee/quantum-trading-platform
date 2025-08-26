package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;

import java.time.Instant;

/**
 * 백업 코드 사용 Event
 * 
 * 2FA 로그인 시 백업 코드가 사용되었을 때 발행되는 이벤트
 */
public record BackupCodeUsedEvent(
    UserId userId,
    String backupCodeHash,
    String ipAddress,
    String userAgent,
    Instant usedAt,
    int remainingBackupCodes
) {
    
    public static BackupCodeUsedEvent of(UserId userId, String backupCodeHash, String ipAddress, 
                                       String userAgent, int remainingBackupCodes) {
        return new BackupCodeUsedEvent(userId, backupCodeHash, ipAddress, userAgent, 
                                     Instant.now(), remainingBackupCodes);
    }
}