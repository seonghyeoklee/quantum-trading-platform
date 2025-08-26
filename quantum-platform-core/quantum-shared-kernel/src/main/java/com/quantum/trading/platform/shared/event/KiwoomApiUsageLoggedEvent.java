package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.KiwoomAccountId;
import java.time.Instant;

/**
 * 키움증권 API 사용 내역이 기록되었을 때 발생하는 Event
 * 
 * - userId: API를 사용한 사용자 ID
 * - kiwoomAccountId: 사용된 키움증권 계좌번호
 * - apiEndpoint: 호출된 API 엔드포인트
 * - requestSize: 요청 데이터 크기 (bytes)
 * - success: API 호출 성공 여부
 * - usageTimestamp: API 사용 시점
 */
public record KiwoomApiUsageLoggedEvent(
    UserId userId,
    KiwoomAccountId kiwoomAccountId,
    String apiEndpoint,
    long requestSize,
    boolean success,
    Instant usageTimestamp
) {
    public KiwoomApiUsageLoggedEvent {
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        
        if (kiwoomAccountId == null) {
            throw new IllegalArgumentException("KiwoomAccountId cannot be null");
        }
        
        if (apiEndpoint == null || apiEndpoint.trim().isEmpty()) {
            throw new IllegalArgumentException("API endpoint cannot be null or empty");
        }
        
        if (requestSize < 0) {
            throw new IllegalArgumentException("Request size cannot be negative");
        }
        
        if (usageTimestamp == null) {
            throw new IllegalArgumentException("Usage timestamp cannot be null");
        }
    }
    
    public static KiwoomApiUsageLoggedEvent createNow(
        UserId userId,
        KiwoomAccountId kiwoomAccountId,
        String apiEndpoint,
        long requestSize,
        boolean success
    ) {
        return new KiwoomApiUsageLoggedEvent(
            userId,
            kiwoomAccountId,
            apiEndpoint,
            requestSize,
            success,
            Instant.now()
        );
    }
}