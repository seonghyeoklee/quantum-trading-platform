package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 사용자 로그인 실패 이벤트
 * 
 * 사용자 로그인 시도가 실패했을 때 발행되는 보안 이벤트
 */
@Value
@Builder
public class UserLoginFailedEvent {
    UserId userId;  // nullable - 사용자를 찾을 수 없는 경우
    String username;
    String reason;
    String ipAddress;
    String userAgent;
    Integer failedAttempts;  // 누적 실패 횟수
    Instant attemptTime;
    boolean accountLocked;
    
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