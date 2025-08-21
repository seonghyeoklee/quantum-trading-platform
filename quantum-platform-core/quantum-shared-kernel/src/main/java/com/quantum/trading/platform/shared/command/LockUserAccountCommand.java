package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 사용자 계정 잠금 커맨드
 * 
 * 보안상의 이유로 사용자 계정을 잠그는 커맨드
 */
@Value
@Builder
public class LockUserAccountCommand {
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    UserId userId;
    
    @NotBlank(message = "Lock reason cannot be null or empty")
    @Size(max = 100, message = "Reason cannot exceed 100 characters")
    String reason;
    
    @Size(max = 500, message = "Details cannot exceed 500 characters")
    String details;
    
    UserId lockedBy;  // nullable - 시스템 자동 잠금인 경우
}