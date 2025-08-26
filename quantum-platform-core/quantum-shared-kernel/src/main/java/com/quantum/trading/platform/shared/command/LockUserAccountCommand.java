package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 사용자 계정 잠금 커맨드
 * 
 * 보안상의 이유로 사용자 계정을 잠그는 커맨드
 */
public record LockUserAccountCommand(
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    UserId userId,
    
    @NotBlank(message = "Lock reason cannot be null or empty")
    @Size(max = 100, message = "Reason cannot exceed 100 characters")
    String reason,
    
    @Size(max = 500, message = "Details cannot exceed 500 characters")
    String details,
    
    UserId lockedBy  // nullable - 시스템 자동 잠금인 경우
) {
    
    /**
     * Compact constructor with validation and normalization
     */
    public LockUserAccountCommand {
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        
        if (reason == null || reason.trim().isEmpty()) {
            throw new IllegalArgumentException("Lock reason cannot be null or empty");
        }
        
        // 정규화
        reason = reason.trim();
        details = details != null ? details.trim() : null;
        
        // 길이 제한 검증
        if (reason.length() > 100) {
            throw new IllegalArgumentException("Reason cannot exceed 100 characters");
        }
        
        if (details != null && details.length() > 500) {
            throw new IllegalArgumentException("Details cannot exceed 500 characters");
        }
    }
    
    /**
     * Factory method for manual lock
     */
    public static LockUserAccountCommand createManualLock(UserId userId, String reason, String details, UserId lockedBy) {
        return new LockUserAccountCommand(userId, reason, details, lockedBy);
    }
    
    /**
     * Factory method for system auto-lock
     */
    public static LockUserAccountCommand createSystemLock(UserId userId, String reason, String details) {
        return new LockUserAccountCommand(userId, reason, details, null);
    }
    
    /**
     * Enum for standardizing lock reasons
     */
    public enum LockReason {
        TOO_MANY_FAILED_ATTEMPTS("Too many failed login attempts"),
        SUSPICIOUS_ACTIVITY("Suspicious account activity detected"),
        SECURITY_VIOLATION("Security policy violation"),
        ADMIN_REQUESTED("Administrator requested lock"),
        MAINTENANCE("System maintenance");
        
        private final String description;
        
        LockReason(String description) {
            this.description = description;
        }
        
        public String getDescription() {
            return description;
        }
    }
}