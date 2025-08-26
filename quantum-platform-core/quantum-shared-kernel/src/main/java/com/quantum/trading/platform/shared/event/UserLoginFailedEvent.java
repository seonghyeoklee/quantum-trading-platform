package com.quantum.trading.platform.shared.event;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;

import java.time.Instant;

/**
 * 사용자 로그인 실패 이벤트
 * <p>
 * 사용자 로그인 시도가 실패했을 때 발행되는 보안 이벤트
 *
 * @param userId         nullable - 사용자를 찾을 수 없는 경우
 * @param failedAttempts 누적 실패 횟수
 */
@Builder
public record UserLoginFailedEvent(@JsonProperty("userId") UserId userId, @JsonProperty("username") String username,
                                   @JsonProperty("reason") String reason, @JsonProperty("ipAddress") String ipAddress,
                                   @JsonProperty("userAgent") String userAgent,
                                   @JsonProperty("failedAttempts") Integer failedAttempts,
                                   @JsonProperty("attemptTime") Instant attemptTime,
                                   @JsonProperty("accountLocked") boolean accountLocked) {

    @JsonCreator
    public UserLoginFailedEvent {
    }

    public static UserLoginFailedEvent create(
            UserId userId,
            String username,
            String reason,
            String ipAddress,
            String userAgent,
            Integer failedAttempts,
            boolean accountLocked) {
        return UserLoginFailedEvent.builder()
                .userId(userId)
                .username(username)
                .reason(reason)
                .ipAddress(ipAddress)
                .userAgent(userAgent)
                .failedAttempts(failedAttempts)
                .attemptTime(Instant.now())
                .accountLocked(accountLocked)
                .build();
    }
}
