package com.quantum.trading.platform.shared.command;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 사용자 인증 커맨드
 * 
 * 사용자 로그인 시도를 처리하는 커맨드
 */
public record AuthenticateUserCommand(
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    @JsonProperty("userId")
    UserId userId,
    
    @NotBlank(message = "Username cannot be null or empty")
    @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
    @JsonProperty("username")
    String username,
    
    @NotNull(message = "Password cannot be null")
    @JsonProperty("password")
    String password, // 이미 해시된 비밀번호이거나 검증된 상태
    
    @NotBlank(message = "Session ID cannot be null or empty")
    @JsonProperty("sessionId")
    String sessionId,
    
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
    public AuthenticateUserCommand {
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        
        if (username == null || username.trim().isEmpty()) {
            throw new IllegalArgumentException("Username cannot be null or empty");
        }
        
        if (password == null) {
            throw new IllegalArgumentException("Password cannot be null");
        }
        
        if (sessionId == null || sessionId.trim().isEmpty()) {
            throw new IllegalArgumentException("Session ID cannot be null or empty");
        }
        
        if (ipAddress == null || ipAddress.trim().isEmpty()) {
            throw new IllegalArgumentException("IP address cannot be null or empty");
        }
        
        // 정규화
        username = username.trim();
        sessionId = sessionId.trim();
        ipAddress = ipAddress.trim();
        userAgent = userAgent != null ? userAgent.trim() : null;
        
        // 길이 제한 검증
        if (username.length() < 3 || username.length() > 50) {
            throw new IllegalArgumentException("Username must be between 3 and 50 characters");
        }
        
        if (userAgent != null && userAgent.length() > 500) {
            throw new IllegalArgumentException("User agent cannot exceed 500 characters");
        }
    }
    
    /**
     * Factory method for creating authentication command
     */
    public static AuthenticateUserCommand create(UserId userId, String username, String password, 
                                               String sessionId, String ipAddress, String userAgent) {
        return new AuthenticateUserCommand(userId, username, password, sessionId, ipAddress, userAgent);
    }
    
    /**
     * Builder pattern support for test compatibility
     */
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private UserId userId;
        private String username;
        private String password;
        private String sessionId;
        private String ipAddress;
        private String userAgent;
        
        public Builder userId(UserId userId) {
            this.userId = userId;
            return this;
        }
        
        public Builder username(String username) {
            this.username = username;
            return this;
        }
        
        public Builder password(String password) {
            this.password = password;
            return this;
        }
        
        public Builder sessionId(String sessionId) {
            this.sessionId = sessionId;
            return this;
        }
        
        public Builder ipAddress(String ipAddress) {
            this.ipAddress = ipAddress;
            return this;
        }
        
        public Builder userAgent(String userAgent) {
            this.userAgent = userAgent;
            return this;
        }
        
        public AuthenticateUserCommand build() {
            return new AuthenticateUserCommand(userId, username, password, sessionId, ipAddress, userAgent);
        }
    }
}