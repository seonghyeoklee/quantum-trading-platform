package com.quantum.trading.platform.shared.event;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;

import java.time.Instant;

/**
 * 로그인 실패 횟수 초기화 이벤트
 * 
 * 로그인 성공 시 실패 횟수가 0으로 리셋되었음을 나타내는 이벤트
 */
@Builder
public record LoginFailureCountResetEvent(
    @JsonProperty("userId")
    UserId userId,
    
    @JsonProperty("username")
    String username,
    
    @JsonProperty("previousFailureCount")
    int previousFailureCount,
    
    @JsonProperty("reason")
    String reason,
    
    @JsonProperty("resetAt")
    Instant resetAt
) {
    
    /**
     * Compact constructor with validation
     */
    public LoginFailureCountResetEvent {
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        
        if (username == null || username.trim().isEmpty()) {
            throw new IllegalArgumentException("Username cannot be null or empty");
        }
        
        if (previousFailureCount < 0) {
            throw new IllegalArgumentException("Previous failure count cannot be negative");
        }
        
        if (resetAt == null) {
            throw new IllegalArgumentException("Reset time cannot be null");
        }
        
        // 정규화
        username = username.trim();
        reason = reason != null ? reason.trim() : "Login success";
    }
    
    /**
     * Factory method for creating reset event with current timestamp
     */
    public static LoginFailureCountResetEvent create(UserId userId, String username, 
                                                   int previousFailureCount, String reason) {
        return new LoginFailureCountResetEvent(userId, username, previousFailureCount, reason, Instant.now());
    }
    
    /**
     * Factory method for creating reset event with default reason
     */
    public static LoginFailureCountResetEvent create(UserId userId, String username, int previousFailureCount) {
        return create(userId, username, previousFailureCount, "Login success");
    }
    
    /**
     * Factory method for creating reset event for successful login
     */
    public static LoginFailureCountResetEvent createForSuccessfulLogin(UserId userId, String username, 
                                                                      int previousFailureCount) {
        return create(userId, username, previousFailureCount, "Login success - failure count reset");
    }
    
    /**
     * Factory method for creating reset event for 2FA completion
     */
    public static LoginFailureCountResetEvent createFor2FACompletion(UserId userId, String username, 
                                                                    int previousFailureCount) {
        return create(userId, username, previousFailureCount, "2FA authentication success - failure count reset");
    }
}