package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 로그인 실패 기록 커맨드
 * 
 * Application Layer에서 비밀번호 검증 실패 시 사용
 * Aggregate에서는 실패 횟수만 기록하고 계정 잠금 여부 판단
 */
@Value
@Builder
public class RecordLoginFailureCommand {
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    UserId userId;
    
    @NotBlank(message = "Failure reason cannot be null or empty")
    @Size(max = 200, message = "Reason cannot exceed 200 characters")
    String reason;
    
    @NotBlank(message = "IP address cannot be null or empty")
    String ipAddress;
    
    @Size(max = 500, message = "User agent cannot exceed 500 characters")
    String userAgent;
}