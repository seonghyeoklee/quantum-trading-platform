package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 사용자 권한 부여 커맨드
 * 
 * 사용자에게 새로운 역할을 부여하는 커맨드
 */
@Value
@Builder
public class GrantUserRoleCommand {
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    UserId userId;
    
    @NotBlank(message = "Role name cannot be null or empty")
    @Pattern(regexp = "ROLE_[A-Z_]+", message = "Role name must start with ROLE_ and contain only uppercase letters and underscores")
    String roleName;
    
    @NotNull(message = "GrantedBy user ID cannot be null")
    UserId grantedBy;
    
    @Size(max = 500, message = "Reason cannot exceed 500 characters")
    String reason;
}