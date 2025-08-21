package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 사용자 로그인 성공 이벤트
 * 
 * 사용자가 성공적으로 로그인했을 때 발행되는 보안 이벤트
 */
@Value
@Builder
public class UserLoginSucceededEvent {
    UserId userId;
    String username;
    String sessionId;
    String ipAddress;
    String userAgent;
    Instant loginTime;
    Instant previousLoginTime;
    
    public static UserLoginSucceededEvent create(
            UserId userId,
            String username,
            String sessionId,
            String ipAddress,
            String userAgent,
            Instant previousLoginTime) {
        return UserLoginSucceededEvent.builder()
                .userId(userId)
                .username(username)
                .sessionId(sessionId)
                .ipAddress(ipAddress)
                .userAgent(userAgent)
                .loginTime(Instant.now())
                .previousLoginTime(previousLoginTime)
                .build();
    }
}