package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.KiwoomAccountId;
import java.time.Instant;

/**
 * 사용자의 키움증권 계좌 할당이 취소되었을 때 발생하는 Event
 * 
 * - userId: 대상 사용자 ID
 * - kiwoomAccountId: 취소된 키움증권 계좌번호
 * - reason: 취소 사유 (선택적)
 * - revokedAt: 취소 시점
 */
public record KiwoomAccountRevokedEvent(
    UserId userId,
    KiwoomAccountId kiwoomAccountId,
    String reason,
    Instant revokedAt
) {
    public KiwoomAccountRevokedEvent {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        
        if (kiwoomAccountId == null) {
            throw new IllegalArgumentException("KiwoomAccountId cannot be null");
        }
        
        if (revokedAt == null) {
            throw new IllegalArgumentException("Revoked timestamp cannot be null");
        }
    }
    
    public static KiwoomAccountRevokedEvent createNow(
        UserId userId,
        KiwoomAccountId kiwoomAccountId,
        String reason
    ) {
        return new KiwoomAccountRevokedEvent(
            userId,
            kiwoomAccountId,
            reason,
            Instant.now()
        );
    }
}