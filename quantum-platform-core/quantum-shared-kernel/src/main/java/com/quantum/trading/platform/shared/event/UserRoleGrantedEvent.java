package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 사용자 권한 부여 이벤트
 * 
 * 사용자에게 새로운 역할/권한이 부여되었을 때 발행되는 이벤트
 */
@Value
@Builder
public class UserRoleGrantedEvent {
    UserId userId;
    String username;
    String roleName;
    UserId grantedBy;
    String grantedByUsername;
    String reason;
    Instant grantedAt;
    
    public static UserRoleGrantedEvent create(
            UserId userId,
            String username,
            String roleName,
            UserId grantedBy,
            String grantedByUsername,
            String reason) {
        return UserRoleGrantedEvent.builder()
                .userId(userId)
                .username(username)
                .roleName(roleName)
                .grantedBy(grantedBy)
                .grantedByUsername(grantedByUsername)
                .reason(reason)
                .grantedAt(Instant.now())
                .build();
    }
}