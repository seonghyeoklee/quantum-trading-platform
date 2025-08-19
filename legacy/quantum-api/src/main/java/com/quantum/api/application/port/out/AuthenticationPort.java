package com.quantum.api.application.port.out;

/** 인증 서비스 공통 인터페이스 */
public interface AuthenticationPort {

    /** 유효한 액세스 토큰 조회 */
    String getValidAccessToken();

    /** 토큰 갱신 */
    String refreshAccessToken();

    /** 토큰 갱신 필요 여부 확인 */
    boolean isTokenRefreshRequired();

    /** 서비스 상태 확인 */
    boolean isHealthy();
}
