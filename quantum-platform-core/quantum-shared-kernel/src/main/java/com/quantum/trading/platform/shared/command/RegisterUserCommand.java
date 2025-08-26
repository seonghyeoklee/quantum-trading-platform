package com.quantum.trading.platform.shared.command;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;
import java.util.Set;
import java.util.HashSet;

/**
 * 사용자 등록 커맨드
 * 
 * 새로운 사용자를 시스템에 등록하는 커맨드
 */
public record RegisterUserCommand(
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    @JsonProperty("userId")
    UserId userId,
    
    @NotBlank(message = "Username cannot be null or empty")
    @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
    @JsonProperty("username")
    String username,
    
    @NotBlank(message = "Password cannot be null or empty")
    @Size(min = 8, max = 100, message = "Password must be between 8 and 100 characters")
    @JsonProperty("password")
    String password,
    
    @NotBlank(message = "Name cannot be null or empty")
    @Size(max = 100, message = "Name cannot exceed 100 characters")
    @JsonProperty("name")
    String name,
    
    @NotBlank(message = "Email cannot be null or empty")
    @Email(message = "Email must be valid")
    @Size(max = 100, message = "Email cannot exceed 100 characters")
    @JsonProperty("email")
    String email,
    
    @Size(max = 20, message = "Phone cannot exceed 20 characters")
    @JsonProperty("phone")
    String phone,
    
    @NotEmpty(message = "At least one role must be specified")
    @JsonProperty("initialRoles")
    Set<String> initialRoles,
    
    @JsonProperty("registeredBy")
    UserId registeredBy
) {
    
    /**
     * Compact constructor with validation and normalization
     */
    public RegisterUserCommand {
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        
        if (username == null || username.trim().isEmpty()) {
            throw new IllegalArgumentException("Username cannot be null or empty");
        }
        
        if (password == null || password.trim().isEmpty()) {
            throw new IllegalArgumentException("Password cannot be null or empty");
        }
        
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("Name cannot be null or empty");
        }
        
        if (email == null || email.trim().isEmpty()) {
            throw new IllegalArgumentException("Email cannot be null or empty");
        }
        
        if (initialRoles == null || initialRoles.isEmpty()) {
            throw new IllegalArgumentException("At least one role must be specified");
        }
        
        // 정규화
        username = username.trim();
        password = password.trim();
        name = name.trim();
        email = email.trim().toLowerCase();
        phone = phone != null ? phone.trim() : null;
        initialRoles = new HashSet<>(initialRoles);
        
        // 길이 제한 검증
        if (username.length() < 3 || username.length() > 50) {
            throw new IllegalArgumentException("Username must be between 3 and 50 characters");
        }
        
        if (password.length() < 8 || password.length() > 100) {
            throw new IllegalArgumentException("Password must be between 8 and 100 characters");
        }
        
        if (name.length() > 100) {
            throw new IllegalArgumentException("Name cannot exceed 100 characters");
        }
        
        if (email.length() > 100) {
            throw new IllegalArgumentException("Email cannot exceed 100 characters");
        }
        
        if (phone != null && phone.length() > 20) {
            throw new IllegalArgumentException("Phone cannot exceed 20 characters");
        }
    }
    
    /**
     * Factory method for creating user registration command
     */
    public static RegisterUserCommand create(UserId userId, String username, String password, 
                                           String name, String email, String phone, 
                                           Set<String> initialRoles, UserId registeredBy) {
        return new RegisterUserCommand(userId, username, password, name, email, phone, initialRoles, registeredBy);
    }
    
    /**
     * Enum for standardizing user roles
     */
    public enum UserRole {
        ADMIN("관리자"),
        TRADER("트레이더"),
        VIEWER("조회자");
        
        private final String description;
        
        UserRole(String description) {
            this.description = description;
        }
        
        public String getDescription() {
            return description;
        }
    }
}