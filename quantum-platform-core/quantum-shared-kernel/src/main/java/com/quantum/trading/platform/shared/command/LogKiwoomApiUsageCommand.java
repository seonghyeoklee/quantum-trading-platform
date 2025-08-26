package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.KiwoomAccountId;

/**
 * 키움증권 API 사용 내역을 로그에 기록하는 Command
 * 
 * - userId: API를 사용한 사용자 ID
 * - kiwoomAccountId: 사용된 키움증권 계좌번호
 * - apiEndpoint: 호출된 API 엔드포인트
 * - requestSize: 요청 데이터 크기 (bytes)
 * - success: API 호출 성공 여부
 */
public record LogKiwoomApiUsageCommand(
    UserId userId,
    KiwoomAccountId kiwoomAccountId,
    String apiEndpoint,
    long requestSize,
    boolean success
) {
    public LogKiwoomApiUsageCommand {
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
    }
    
    public void validate() {
        // Additional business validation logic
        if (apiEndpoint.trim().length() > 200) {
            throw new IllegalArgumentException("API endpoint is too long (max 200 characters)");
        }
    }
}