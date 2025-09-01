package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.KiwoomAccountId;
import java.time.Instant;

/**
 * 사용자에게 키움증권 계좌가 할당되었을 때 발생하는 Event
 * 
 * - userId: 할당받은 사용자 ID
 * - kiwoomAccountId: 할당된 키움증권 계좌번호
 * - clientId: 클라이언트 ID (plain text)
 * - clientSecret: 클라이언트 시크릿 (plain text)
 * - assignedAt: 할당 시점
 */
public record KiwoomAccountAssignedEvent(
    UserId userId,
    KiwoomAccountId kiwoomAccountId,
    String clientId,
    String clientSecret,
    Instant assignedAt
) {
    public KiwoomAccountAssignedEvent {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        
        if (kiwoomAccountId == null) {
            throw new IllegalArgumentException("KiwoomAccountId cannot be null");
        }
        
        if (clientId == null || clientId.trim().isEmpty()) {
            throw new IllegalArgumentException("ClientId cannot be null or empty");
        }
        
        if (clientSecret == null || clientSecret.trim().isEmpty()) {
            throw new IllegalArgumentException("ClientSecret cannot be null or empty");
        }
        
        if (assignedAt == null) {
            throw new IllegalArgumentException("Assigned timestamp cannot be null");
        }
    }
    
    public static KiwoomAccountAssignedEvent createNow(
        UserId userId,
        KiwoomAccountId kiwoomAccountId,
        String clientId,
        String clientSecret
    ) {
        return new KiwoomAccountAssignedEvent(
            userId,
            kiwoomAccountId,
            clientId,
            clientSecret,
            Instant.now()
        );
    }
}