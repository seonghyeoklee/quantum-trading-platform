package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 사용자 인증 커맨드
 * 
 * 사용자 로그인 시도를 처리하는 커맨드
 */
@Value
@Builder
public class AuthenticateUserCommand {
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    UserId userId;
    
    @NotBlank(message = "Username cannot be null or empty")
    @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
    String username;
    
    @NotNull(message = "Password cannot be null")
    String password; // 이미 해시된 비밀번호이거나 검증된 상태
    
    @NotBlank(message = "Session ID cannot be null or empty")
    String sessionId;
    
    @NotBlank(message = "IP address cannot be null or empty")
    String ipAddress;
    
    @Size(max = 500, message = "User agent cannot exceed 500 characters")
    String userAgent;
}