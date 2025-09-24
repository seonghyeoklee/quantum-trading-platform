package com.quantum.kis.application.port.out;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;

/**
 * 알림 포트
 * 토큰 관련 이벤트 알림을 추상화
 */
public interface NotificationPort {

    /**
     * 토큰 재발급 알림을 보낸다.
     * @param environment KIS 환경
     * @param tokenType 토큰 타입
     */
    void notifyTokenRefreshed(KisEnvironment environment, TokenType tokenType);

    /**
     * 토큰 만료 알림을 보낸다.
     * @param environment KIS 환경
     * @param tokenType 토큰 타입
     */
    void notifyTokenExpired(KisEnvironment environment, TokenType tokenType);

    /**
     * 토큰 발급 실패 알림을 보낸다.
     * @param environment KIS 환경
     * @param tokenType 토큰 타입
     * @param errorMessage 오류 메시지
     */
    void notifyTokenIssueFailed(KisEnvironment environment, TokenType tokenType, String errorMessage);
}