package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import java.time.Instant;

/**
 * 사용자의 키움증권 API 인증 정보가 업데이트되었을 때 발생하는 Event
 * 
 * - userId: 대상 사용자 ID
 * - newClientId: 새로운 클라이언트 ID (plain text)
 * - newClientSecret: 새로운 클라이언트 시크릿 (plain text)
 * - updatedAt: 업데이트 시점
 */
public record KiwoomCredentialsUpdatedEvent(
    UserId userId,
    String newClientId,
    String newClientSecret,
    Instant updatedAt
) {
    public KiwoomCredentialsUpdatedEvent {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        
        if (newClientId == null || newClientId.trim().isEmpty()) {
            throw new IllegalArgumentException("New client ID cannot be null or empty");
        }
        
        if (newClientSecret == null || newClientSecret.trim().isEmpty()) {
            throw new IllegalArgumentException("New client secret cannot be null or empty");
        }
        
        if (updatedAt == null) {
            throw new IllegalArgumentException("Updated timestamp cannot be null");
        }
    }
    
    public static KiwoomCredentialsUpdatedEvent createNow(
        UserId userId,
        String newClientId,
        String newClientSecret
    ) {
        return new KiwoomCredentialsUpdatedEvent(
            userId,
            newClientId,
            newClientSecret,
            Instant.now()
        );
    }
}