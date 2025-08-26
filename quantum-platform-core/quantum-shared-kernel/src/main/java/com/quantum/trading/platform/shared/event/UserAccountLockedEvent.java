package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;

import java.time.Instant;

/**
 * 사용자 계정 잠금 이벤트
 * <p>
 * 사용자 계정이 보안상의 이유로 잠겼을 때 발행되는 이벤트
 *
 * @param reason           "TOO_MANY_FAILED_ATTEMPTS", "SUSPICIOUS_ACTIVITY", "ADMIN_ACTION"
 * @param lockedBy         nullable - 시스템 자동 잠금인 경우
 * @param lockedByUsername nullable
 * @param unlockAfter      nullable - 자동 해제 시간
 */
@Builder
public record UserAccountLockedEvent(UserId userId, String username, String reason, String details, UserId lockedBy,
                                     String lockedByUsername, Instant lockedAt, Instant unlockAfter) {

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
