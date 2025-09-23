package com.quantum.kis.domain.token;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;

/**
 * KIS 토큰의 Value Object ID
 * 환경과 토큰 타입의 조합으로 유니크한 식별자 생성
 */
public record KisTokenId(
        KisEnvironment environment,
        TokenType tokenType
) {
    public KisTokenId {
        if (environment == null) {
            throw new IllegalArgumentException("환경은 필수입니다.");
        }
        if (tokenType == null) {
            throw new IllegalArgumentException("토큰 타입은 필수입니다.");
        }
    }

    /**
     * 문자열 키 생성 (DB 저장용)
     * @return "환경_토큰타입" 형태의 키
     */
    public String toKey() {
        return environment.name() + "_" + tokenType.name();
    }

    /**
     * 문자열 키로부터 KisTokenId 생성
     * @param key "환경_토큰타입" 형태의 키
     * @return KisTokenId 객체
     */
    public static KisTokenId fromKey(String key) {
        if (key == null || key.isBlank()) {
            throw new IllegalArgumentException("키는 필수입니다.");
        }

        String[] parts = key.split("_");
        if (parts.length != 2) {
            throw new IllegalArgumentException("잘못된 키 형식입니다: " + key);
        }

        try {
            KisEnvironment environment = KisEnvironment.valueOf(parts[0]);
            TokenType tokenType = TokenType.valueOf(parts[1]);
            return new KisTokenId(environment, tokenType);
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("키 파싱 실패: " + key, e);
        }
    }

    @Override
    public String toString() {
        return toKey();
    }
}