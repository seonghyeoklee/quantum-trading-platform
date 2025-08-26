package com.quantum.trading.platform.shared.event;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;

import java.time.Instant;

/**
 * 사용자 로그아웃 이벤트
 * <p>
 * 사용자가 로그아웃하거나 세션이 만료되었을 때 발행되는 이벤트
 *
 * @param reason          "USER_LOGOUT", "SESSION_EXPIRED", "ADMIN_FORCED", etc.
 * @param sessionDuration 총 세션 지속 시간 계산용
 */
@Builder
public record UserLoggedOutEvent(UserId userId, String username, String sessionId, String reason, String ipAddress,
                                 Instant logoutTime, Instant sessionDuration) {

    @JsonCreator
    public UserLoggedOutEvent(
            @JsonProperty("userId") UserId userId,
            @JsonProperty("username") String username,
            @JsonProperty("sessionId") String sessionId,
            @JsonProperty("reason") String reason,
            @JsonProperty("ipAddress") String ipAddress,
            @JsonProperty("logoutTime") Instant logoutTime,
            @JsonProperty("sessionDuration") Instant sessionDuration) {
        this.userId = userId;
        this.username = username;
        this.sessionId = sessionId;
        this.reason = reason;
        this.ipAddress = ipAddress;
        this.logoutTime = logoutTime;
        this.sessionDuration = sessionDuration;
    }

    public static UserLoggedOutEvent create(
            UserId userId,
            String username,
            String sessionId,
            String reason,
            String ipAddress,
            Instant sessionStartTime) {
        Instant logoutTime = Instant.now();
        return UserLoggedOutEvent.builder()
                .userId(userId)
                .username(username)
                .sessionId(sessionId)
                .reason(reason)
                .ipAddress(ipAddress)
                .logoutTime(logoutTime)
                .sessionDuration(sessionStartTime != null ?
                        logoutTime.minusSeconds(sessionStartTime.getEpochSecond()) : null)
                .build();
    }
}
