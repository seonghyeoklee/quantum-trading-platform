package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

/**
 * 백업 코드 사용 Command
 * 
 * 2FA 로그인 시 백업 코드를 사용하는 명령
 */
public record UseBackupCodeCommand(
    @TargetAggregateIdentifier
    UserId userId,
    String backupCodeHash,
    String ipAddress,
    String userAgent
) {
    
    public static UseBackupCodeCommand of(UserId userId, String backupCodeHash, String ipAddress, String userAgent) {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        if (backupCodeHash == null || backupCodeHash.trim().isEmpty()) {
            throw new IllegalArgumentException("Backup code hash cannot be null or empty");
        }
        
        return new UseBackupCodeCommand(userId, backupCodeHash.trim(), ipAddress, userAgent);
    }
    
    /**
     * Command 검증
     */
    public void validate() {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        if (backupCodeHash == null || backupCodeHash.trim().isEmpty()) {
            throw new IllegalArgumentException("Backup code hash cannot be null or empty");
        }
    }
}