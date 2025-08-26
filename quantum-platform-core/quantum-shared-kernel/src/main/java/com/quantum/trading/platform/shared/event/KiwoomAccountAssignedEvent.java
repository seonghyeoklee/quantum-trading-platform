package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.KiwoomAccountId;
import com.quantum.trading.platform.shared.value.EncryptedValue;
import java.time.Instant;

/**
 * 사용자에게 키움증권 계좌가 할당되었을 때 발생하는 Event
 * 
 * - userId: 할당받은 사용자 ID
 * - kiwoomAccountId: 할당된 키움증권 계좌번호
 * - encryptedCredentials: 암호화된 API 인증 정보
 * - assignedAt: 할당 시점
 */
public record KiwoomAccountAssignedEvent(
    UserId userId,
    KiwoomAccountId kiwoomAccountId,
    EncryptedValue encryptedCredentials,
    Instant assignedAt
) {
    public KiwoomAccountAssignedEvent {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        
        if (kiwoomAccountId == null) {
            throw new IllegalArgumentException("KiwoomAccountId cannot be null");
        }
        
        if (encryptedCredentials == null) {
            throw new IllegalArgumentException("Encrypted credentials cannot be null");
        }
        
        if (assignedAt == null) {
            throw new IllegalArgumentException("Assigned timestamp cannot be null");
        }
    }
    
    public static KiwoomAccountAssignedEvent createNow(
        UserId userId,
        KiwoomAccountId kiwoomAccountId,
        EncryptedValue encryptedCredentials
    ) {
        return new KiwoomAccountAssignedEvent(
            userId,
            kiwoomAccountId,
            encryptedCredentials,
            Instant.now()
        );
    }
}