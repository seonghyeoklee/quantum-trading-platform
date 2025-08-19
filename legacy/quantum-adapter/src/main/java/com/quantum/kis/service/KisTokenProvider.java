package com.quantum.kis.service;

/**
 * KIS 토큰 제공자 인터페이스
 *
 * <p>quantum-adapter가 quantum-batch에 직접 의존하지 않도록 하는 인터페이스 실제 구현체는 각 모듈에서 제공
 */
public interface KisTokenProvider {

    /**
     * 유효한 액세스 토큰 조회
     *
     * @return 유효한 액세스 토큰, 실패시 null
     */
    String getValidAccessToken();

    /**
     * API 호출 전 Rate Limiting 체크
     *
     * @param apiEndpoint API 엔드포인트 구분자
     * @return 호출 가능하면 true, 제한에 걸리면 false
     */
    boolean checkRateLimit(String apiEndpoint);

    /**
     * 강제 대기 후 API 호출 (재시도 포함)
     *
     * @param apiEndpoint API 엔드포인트 구분자
     * @return 호출 가능하면 true, 최종 실패시 false
     */
    boolean acquireWithWait(String apiEndpoint);
}
