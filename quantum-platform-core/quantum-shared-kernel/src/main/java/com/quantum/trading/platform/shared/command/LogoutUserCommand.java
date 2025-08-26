package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.*;

/**
 * 사용자 로그아웃 커맨드
 *
 * 사용자 세션을 종료하는 커맨드
 */
public record LogoutUserCommand(
    @TargetAggregateIdentifier
    @NotNull(message = "User ID cannot be null")
    UserId userId,

    @NotBlank(message = "Session ID cannot be null or empty")
    String sessionId,

    @NotBlank(message = "Logout reason cannot be null or empty")
    @Pattern(regexp = "USER_LOGOUT|SESSION_EXPIRED|ADMIN_FORCED",
             message = "Reason must be one of: USER_LOGOUT, SESSION_EXPIRED, ADMIN_FORCED")
    String reason,

    @NotBlank(message = "IP address cannot be null or empty")
    String ipAddress
) {

    /**
     * Compact constructor with validation
     */
    public LogoutUserCommand {
        // 추가 비즈니스 검증 로직
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }

        if (sessionId == null || sessionId.trim().isEmpty()) {
            throw new IllegalArgumentException("Session ID cannot be null or empty");
        }

        if (reason == null || reason.trim().isEmpty()) {
            throw new IllegalArgumentException("Logout reason cannot be null or empty");
        }

        if (ipAddress == null || ipAddress.trim().isEmpty()) {
            throw new IllegalArgumentException("IP address cannot be null or empty");
        }

        // 정규화 처리
        sessionId = sessionId.trim();
        reason = reason.trim().toUpperCase();
        ipAddress = ipAddress.trim();
    }

    /**
     * Enum for standardizing logout reasons
     */
    public enum LogoutReason {
        USER_LOGOUT("User initiated logout"),
        SESSION_EXPIRED("Session expired"),
        ADMIN_FORCED("Administrator forced logout");

        private final String description;

        LogoutReason(String description) {
            this.description = description;
        }

        public String getDescription() {
            return description;
        }
    }

    /**
     * Factory method with enum reason
     */
    public static LogoutUserCommand create(UserId userId, String sessionId, LogoutReason reason, String ipAddress) {
        return new LogoutUserCommand(userId, sessionId, reason.name(), ipAddress);
    }
}
