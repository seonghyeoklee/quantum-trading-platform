package com.quantum.kis.domain.token;

import java.time.LocalDateTime;

/**
 * 토큰 Value Object
 * 토큰의 값과 만료시간을 캡슐화
 */
public record Token(
        String value,
        LocalDateTime expiresAt
) {
    public Token {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("토큰 값은 필수입니다.");
        }
        if (expiresAt == null) {
            throw new IllegalArgumentException("만료 시간은 필수입니다.");
        }
    }

    /**
     * 토큰이 만료되었는지 확인
     * @return 만료된 경우 true
     */
    public boolean isExpired() {
        return LocalDateTime.now().isAfter(expiresAt);
    }

    /**
     * 토큰이 곧 만료될지 확인 (만료 1시간 전)
     * @return 곧 만료될 경우 true
     */
    public boolean isExpiringSoon() {
        return LocalDateTime.now().plusHours(1).isAfter(expiresAt);
    }

    /**
     * 토큰이 유효한지 확인
     * @return 만료되지 않은 경우 true
     */
    public boolean isValid() {
        return !isExpired();
    }

    /**
     * 새 토큰 생성
     * @param value 토큰 값
     * @param expiresAt 만료 시간
     * @return Token 객체
     */
    public static Token of(String value, LocalDateTime expiresAt) {
        return new Token(value, expiresAt);
    }

    /**
     * 기본 만료시간(24시간)으로 토큰 생성
     * @param value 토큰 값
     * @return Token 객체
     */
    public static Token withDefaultExpiry(String value) {
        return new Token(value, LocalDateTime.now().plusHours(24));
    }
}