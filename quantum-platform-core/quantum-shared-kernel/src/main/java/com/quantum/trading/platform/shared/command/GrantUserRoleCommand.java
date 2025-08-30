package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 사용자 권한 부여 커맨드
 * 
 * 사용자에게 새로운 역할을 부여하는 커맨드
 */
public record GrantUserRoleCommand(
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    UserId userId,
    
    @NotBlank(message = "Role name cannot be null or empty")
    @Pattern(regexp = "ROLE_[A-Z_]+", message = "Role name must start with ROLE_ and contain only uppercase letters and underscores")
    String roleName,
    
    @NotNull(message = "GrantedBy user ID cannot be null")
    UserId grantedBy,
    
    @Size(max = 500, message = "Reason cannot exceed 500 characters")
    String reason
) {
    
    /**
     * Compact constructor with validation and normalization
     */
    public GrantUserRoleCommand {
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        
        if (grantedBy == null) {
            throw new IllegalArgumentException("GrantedBy user ID cannot be null");
        }
        
        if (roleName == null || roleName.trim().isEmpty()) {
            throw new IllegalArgumentException("Role name cannot be null or empty");
        }
        
        // 정규화
        roleName = roleName.trim().toUpperCase();
        reason = reason != null ? reason.trim() : null;
        
        // 역할 이름 패턴 검증
        if (!roleName.matches("ROLE_[A-Z_]+")) {
            throw new IllegalArgumentException("Role name must start with ROLE_ and contain only uppercase letters and underscores");
        }
        
        // 길이 제한 검증
        if (reason != null && reason.length() > 500) {
            throw new IllegalArgumentException("Reason cannot exceed 500 characters");
        }
    }
    
    /**
     * Factory method for granting role with reason
     */
    public static GrantUserRoleCommand create(UserId userId, String roleName, UserId grantedBy, String reason) {
        return new GrantUserRoleCommand(userId, roleName, grantedBy, reason);
    }
    
    /**
     * Factory method for granting role without reason
     */
    public static GrantUserRoleCommand create(UserId userId, String roleName, UserId grantedBy) {
        return new GrantUserRoleCommand(userId, roleName, grantedBy, null);
    }
    
    /**
     * Factory method with enum role
     */
    public static GrantUserRoleCommand create(UserId userId, SystemRole role, UserId grantedBy, String reason) {
        return new GrantUserRoleCommand(userId, role.getRoleName(), grantedBy, reason);
    }
    
    /**
     * Builder pattern support for test compatibility
     */
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private UserId userId;
        private String roleName;
        private UserId grantedBy;
        private String reason;
        
        public Builder userId(UserId userId) {
            this.userId = userId;
            return this;
        }
        
        public Builder roleName(String roleName) {
            this.roleName = roleName;
            return this;
        }
        
        public Builder grantedBy(UserId grantedBy) {
            this.grantedBy = grantedBy;
            return this;
        }
        
        public Builder reason(String reason) {
            this.reason = reason;
            return this;
        }
        
        public GrantUserRoleCommand build() {
            return new GrantUserRoleCommand(userId, roleName, grantedBy, reason);
        }
    }
    
    /**
     * Enum for standardizing system roles
     */
    public enum SystemRole {
        ADMIN("ROLE_ADMIN", "시스템 관리자"),
        TRADER("ROLE_TRADER", "트레이더"),
        VIEWER("ROLE_VIEWER", "조회자"),
        ANALYST("ROLE_ANALYST", "분석가"),
        RISK_MANAGER("ROLE_RISK_MANAGER", "리스크 관리자");
        
        private final String roleName;
        private final String description;
        
        SystemRole(String roleName, String description) {
            this.roleName = roleName;
            this.description = description;
        }
        
        public String getRoleName() {
            return roleName;
        }
        
        public String getDescription() {
            return description;
        }
    }
}