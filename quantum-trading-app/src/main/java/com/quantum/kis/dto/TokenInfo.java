package com.quantum.kis.dto;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;

import java.time.LocalDateTime;

/**
 * 토큰 정보 저장용 레코드
 */
public record TokenInfo(
        KisEnvironment environment,     // 환경 (PROD/VPS)
        TokenType tokenType,           // 토큰 타입 (ACCESS_TOKEN/WEBSOCKET_KEY)
        String token,                  // 토큰 값
        LocalDateTime issuedAt,        // 발급 시간
        LocalDateTime expiresAt,       // 만료 시간
        boolean isValid               // 유효성 여부
) {
    /**
     * 토큰이 만료되었는지 확인한다.
     * @return 만료된 경우 true, 유효한 경우 false
     */
    public boolean isExpired() {
        return LocalDateTime.now().isAfter(expiresAt);
    }

    /**
     * 토큰이 곧 만료될지 확인한다 (만료 1시간 전).
     * @return 곧 만료될 경우 true
     */
    public boolean isExpiringSoon() {
        return LocalDateTime.now().plusHours(1).isAfter(expiresAt);
    }

    /**
     * 새 토큰 정보를 생성한다.
     * @param environment 환경
     * @param tokenType 토큰 타입
     * @param token 토큰 값
     * @param expiresAt 만료 시간
     * @return TokenInfo 객체
     */
    public static TokenInfo create(KisEnvironment environment, TokenType tokenType,
                                  String token, LocalDateTime expiresAt) {
        return new TokenInfo(
                environment,
                tokenType,
                token,
                LocalDateTime.now(),
                expiresAt,
                true
        );
    }

    /**
     * 무효한 토큰 정보를 생성한다.
     * @param environment 환경
     * @param tokenType 토큰 타입
     * @return 무효한 TokenInfo 객체
     */
    public static TokenInfo invalid(KisEnvironment environment, TokenType tokenType) {
        return new TokenInfo(
                environment,
                tokenType,
                null,
                null,
                null,
                false
        );
    }
}