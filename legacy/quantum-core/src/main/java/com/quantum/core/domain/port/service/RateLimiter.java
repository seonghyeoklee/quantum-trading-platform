package com.quantum.core.domain.port.service;

/**
 * API Rate Limiting 인터페이스
 * 
 * KIS API 공식 제한 정책:
 * - 실전투자: 1초당 20건 (계좌별)
 * - 모의투자: 1초당 2건 (계좌별)
 * - 토큰발급: 1초당 1건
 */
public interface RateLimiter {

    /**
     * API 호출 전 Rate Limit 체크
     * 
     * @param apiEndpoint API 엔드포인트 식별자
     * @param isTokenRequest 토큰 발급 요청 여부
     * @return 호출 허용 여부
     */
    boolean tryAcquire(String apiEndpoint, boolean isTokenRequest);
    
    /**
     * 강제 대기 후 호출 허용 (재시도 로직)
     * 
     * @param apiEndpoint API 엔드포인트 식별자
     * @param isTokenRequest 토큰 발급 요청 여부
     * @return 호출 허용 여부
     */
    boolean acquireWithWait(String apiEndpoint, boolean isTokenRequest);
    
    /**
     * API 호출 통계 조회 (모니터링용)
     * 
     * @param apiEndpoint API 엔드포인트 식별자
     * @return Rate Limit 상태 정보
     */
    RateLimitStatus getStatus(String apiEndpoint);
    
    /**
     * Rate Limit 상태 정보
     */
    record RateLimitStatus(
            String apiEndpoint,
            long callsLastSecond,
            long callsLastMinute,
            long callsLastHour,
            boolean available
    ) {}
}