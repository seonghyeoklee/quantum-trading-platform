package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.EncryptedValue;
import java.time.Instant;

/**
 * 사용자의 키움증권 API 인증 정보가 업데이트되었을 때 발생하는 Event
 * 
 * - userId: 대상 사용자 ID
 * - newEncryptedCredentials: 새로운 암호화된 API 인증 정보
 * - updatedAt: 업데이트 시점
 */
public record KiwoomCredentialsUpdatedEvent(
    UserId userId,
    EncryptedValue newEncryptedCredentials,
    Instant updatedAt
) {
    public KiwoomCredentialsUpdatedEvent {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        
        if (newEncryptedCredentials == null) {
            throw new IllegalArgumentException("New encrypted credentials cannot be null");
        }
        
        if (updatedAt == null) {
            throw new IllegalArgumentException("Updated timestamp cannot be null");
        }
    }
    
    public static KiwoomCredentialsUpdatedEvent createNow(
        UserId userId,
        EncryptedValue newEncryptedCredentials
    ) {
        return new KiwoomCredentialsUpdatedEvent(
            userId,
            newEncryptedCredentials,
            Instant.now()
        );
    }
}