package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;
import java.util.Set;

/**
 * 사용자 등록 커맨드
 * 
 * 새로운 사용자를 시스템에 등록하는 커맨드
 */
@Value
@Builder
public class RegisterUserCommand {
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    UserId userId;
    
    @NotBlank(message = "Username cannot be null or empty")
    @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
    String username;
    
    @NotBlank(message = "Password cannot be null or empty")
    @Size(min = 8, max = 100, message = "Password must be between 8 and 100 characters")
    String password;
    
    @NotBlank(message = "Name cannot be null or empty")
    @Size(max = 100, message = "Name cannot exceed 100 characters")
    String name;
    
    @NotBlank(message = "Email cannot be null or empty")
    @Email(message = "Email must be valid")
    @Size(max = 100, message = "Email cannot exceed 100 characters")
    String email;
    
    @Size(max = 20, message = "Phone cannot exceed 20 characters")
    String phone;
    
    @NotEmpty(message = "At least one role must be specified")
    Set<String> initialRoles;
    
    UserId registeredBy;
    
}