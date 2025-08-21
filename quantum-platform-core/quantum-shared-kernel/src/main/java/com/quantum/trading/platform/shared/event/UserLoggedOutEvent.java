package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 사용자 로그아웃 이벤트
 * 
 * 사용자가 로그아웃하거나 세션이 만료되었을 때 발행되는 이벤트
 */
@Value
@Builder
public class UserLoggedOutEvent {
    UserId userId;
    String username;
    String sessionId;
    String reason;  // "USER_LOGOUT", "SESSION_EXPIRED", "ADMIN_FORCED", etc.
    String ipAddress;
    Instant logoutTime;
    Instant sessionDuration;  // 총 세션 지속 시간 계산용
    
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