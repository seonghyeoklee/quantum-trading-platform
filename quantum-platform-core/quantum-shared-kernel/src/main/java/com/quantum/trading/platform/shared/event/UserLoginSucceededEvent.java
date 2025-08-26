package com.quantum.trading.platform.shared.event;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
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
    @JsonProperty("userId")
    UserId userId;
    @JsonProperty("username")
    String username;
    @JsonProperty("sessionId")
    String sessionId;
    @JsonProperty("ipAddress")
    String ipAddress;
    @JsonProperty("userAgent")
    String userAgent;
    @JsonProperty("loginTime")
    Instant loginTime;
    @JsonProperty("previousLoginTime")
    Instant previousLoginTime;
    
    @JsonCreator
    public UserLoginSucceededEvent(
            @JsonProperty("userId") UserId userId,
            @JsonProperty("username") String username,
            @JsonProperty("sessionId") String sessionId,
            @JsonProperty("ipAddress") String ipAddress,
            @JsonProperty("userAgent") String userAgent,
            @JsonProperty("loginTime") Instant loginTime,
            @JsonProperty("previousLoginTime") Instant previousLoginTime) {
        this.userId = userId;
        this.username = username;
        this.sessionId = sessionId;
        this.ipAddress = ipAddress;
        this.userAgent = userAgent;
        this.loginTime = loginTime;
        this.previousLoginTime = previousLoginTime;
    }
    
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