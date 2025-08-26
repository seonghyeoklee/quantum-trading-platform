package com.quantum.trading.platform.shared.command;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 로그인 실패 기록 커맨드
 * 
 * Application Layer에서 비밀번호 검증 실패 시 사용
 * Aggregate에서는 실패 횟수만 기록하고 계정 잠금 여부 판단
 */
public record RecordLoginFailureCommand(
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    @JsonProperty("userId")
    UserId userId,
    
    @NotBlank(message = "Failure reason cannot be null or empty")
    @Size(max = 200, message = "Reason cannot exceed 200 characters")
    @JsonProperty("reason")
    String reason,
    
    @NotBlank(message = "IP address cannot be null or empty")
    @JsonProperty("ipAddress")
    String ipAddress,
    
    @Size(max = 500, message = "User agent cannot exceed 500 characters")
    @JsonProperty("userAgent")
    String userAgent
) {
    
    /**
     * Compact constructor with validation and normalization
     */
    public RecordLoginFailureCommand {
        // 유효성 검증
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        
        if (reason == null || reason.trim().isEmpty()) {
            throw new IllegalArgumentException("Failure reason cannot be null or empty");
        }
        
        if (ipAddress == null || ipAddress.trim().isEmpty()) {
            throw new IllegalArgumentException("IP address cannot be null or empty");
        }
        
        // 정규화 (compact constructor에서는 재할당 가능)
        reason = reason.trim();
        ipAddress = ipAddress.trim();
        userAgent = userAgent != null ? userAgent.trim() : null;
        
        // 길이 제한 검증
        if (reason.length() > 200) {
            throw new IllegalArgumentException("Reason cannot exceed 200 characters");
        }
        
        if (userAgent != null && userAgent.length() > 500) {
            throw new IllegalArgumentException("User agent cannot exceed 500 characters");
        }
    }
    
    /**
     * Enum for standardizing failure reasons
     */
    public enum FailureReason {
        INVALID_PASSWORD("Invalid password provided"),
        INVALID_USERNAME("Invalid username provided"),
        ACCOUNT_LOCKED("Account is currently locked"),
        ACCOUNT_DISABLED("Account is disabled"),
        TOO_MANY_ATTEMPTS("Too many login attempts"),
        SUSPICIOUS_ACTIVITY("Suspicious login activity detected");
        
        private final String description;
        
        FailureReason(String description) {
            this.description = description;
        }
        
        public String getDescription() {
            return description;
        }
    }
    
    /**
     * Factory method with enum reason
     */
    public static RecordLoginFailureCommand create(UserId userId, FailureReason reason, String ipAddress, String userAgent) {
        return new RecordLoginFailureCommand(userId, reason.getDescription(), ipAddress, userAgent);
    }
}