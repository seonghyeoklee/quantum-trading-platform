package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 사용자 계정 잠금 이벤트
 * 
 * 사용자 계정이 보안상의 이유로 잠겼을 때 발행되는 이벤트
 */
@Value
@Builder
public class UserAccountLockedEvent {
    UserId userId;
    String username;
    String reason;  // "TOO_MANY_FAILED_ATTEMPTS", "SUSPICIOUS_ACTIVITY", "ADMIN_ACTION"
    String details;
    UserId lockedBy;  // nullable - 시스템 자동 잠금인 경우
    String lockedByUsername;  // nullable
    Instant lockedAt;
    Instant unlockAfter;  // nullable - 자동 해제 시간
    
    public static UserAccountLockedEvent createAutoLock(
            UserId userId,
            String username,
            String reason,
            String details) {
        return UserAccountLockedEvent.builder()
                .userId(userId)
                .username(username)
                .reason(reason)
                .details(details)
                .lockedBy(null)
                .lockedByUsername("SYSTEM")
                .lockedAt(Instant.now())
                .unlockAfter(null)  // 수동 해제 필요
                .build();
    }
    
    public static UserAccountLockedEvent createManualLock(
            UserId userId,
            String username,
            String reason,
            String details,
            UserId lockedBy,
            String lockedByUsername) {
        return UserAccountLockedEvent.builder()
                .userId(userId)
                .username(username)
                .reason(reason)
                .details(details)
                .lockedBy(lockedBy)
                .lockedByUsername(lockedByUsername)
                .lockedAt(Instant.now())
                .unlockAfter(null)
                .build();
    }
}