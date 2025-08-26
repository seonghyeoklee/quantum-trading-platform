package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import java.util.Set;

/**
 * 2FA 활성화 Command
 * 
 * TOTP 인증이 성공한 후 2FA를 활성화하는 명령
 */
public record EnableTwoFactorCommand(
    @TargetAggregateIdentifier
    UserId userId,
    String totpSecretKey,
    Set<String> backupCodeHashes
) {
    
    public static EnableTwoFactorCommand of(UserId userId, String totpSecretKey, Set<String> backupCodeHashes) {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        if (totpSecretKey == null || totpSecretKey.trim().isEmpty()) {
            throw new IllegalArgumentException("TOTP secret key cannot be null or empty");
        }
        if (backupCodeHashes == null || backupCodeHashes.isEmpty()) {
            throw new IllegalArgumentException("Backup code hashes cannot be null or empty");
        }
        
        return new EnableTwoFactorCommand(userId, totpSecretKey.trim(), backupCodeHashes);
    }
    
    /**
     * Command 검증
     */
    public void validate() {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        if (totpSecretKey == null || totpSecretKey.trim().isEmpty()) {
            throw new IllegalArgumentException("TOTP secret key cannot be null or empty");
        }
        if (backupCodeHashes == null || backupCodeHashes.isEmpty()) {
            throw new IllegalArgumentException("Backup code hashes cannot be null or empty");
        }
        if (backupCodeHashes.size() < 8) {
            throw new IllegalArgumentException("At least 8 backup codes are required");
        }
    }
}