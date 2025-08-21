package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 사용자 로그아웃 커맨드
 * 
 * 사용자 세션을 종료하는 커맨드
 */
@Value
@Builder
public class LogoutUserCommand {
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    UserId userId;
    
    @NotBlank(message = "Session ID cannot be null or empty")
    String sessionId;
    
    @NotBlank(message = "Logout reason cannot be null or empty")
    @Pattern(regexp = "USER_LOGOUT|SESSION_EXPIRED|ADMIN_FORCED", 
             message = "Reason must be one of: USER_LOGOUT, SESSION_EXPIRED, ADMIN_FORCED")
    String reason;
    
    @NotBlank(message = "IP address cannot be null or empty")
    String ipAddress;
}