package com.quantum.core.domain.model.common;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * 가격 변동 방향 열거형
 * KIS API 응답의 전일대비 부호를 타입 안전하게 관리
 */
@Getter
@RequiredArgsConstructor
public enum PriceChangeDirection {

    UPPER_LIMIT("1", "상한", "⬆️", true),
    RISE("2", "상승", "🔼", true),
    FLAT("3", "보합", "➡️", false),
    LOWER_LIMIT("4", "하한", "⬇️", false),
    FALL("5", "하락", "🔽", false),
    UNKNOWN("0", "알수없음", "❓", false);

    private final String kisCode;        // KIS API 부호 코드
    private final String koreanName;     // 한글명
    private final String emoji;          // 이모지 표시
    private final boolean isPositive;    // 상승 여부

    /**
     * KIS API 부호 코드로부터 변환
     */
    public static PriceChangeDirection fromKisCode(String kisCode) {
        if (kisCode == null || kisCode.trim().isEmpty()) {
            return UNKNOWN;
        }
        
        for (PriceChangeDirection direction : values()) {
            if (direction.kisCode.equals(kisCode.trim())) {
                return direction;
            }
        }
        
        return UNKNOWN;
    }

    /**
     * 상승/하한 여부
     */
    public boolean isBullish() {
        return this == UPPER_LIMIT || this == RISE;
    }

    /**
     * 하락/하한 여부
     */
    public boolean isBearish() {
        return this == LOWER_LIMIT || this == FALL;
    }

    /**
     * 보합 여부
     */
    public boolean isFlat() {
        return this == FLAT;
    }

    /**
     * 극단적 움직임 여부 (상한/하한)
     */
    public boolean isExtreme() {
        return this == UPPER_LIMIT || this == LOWER_LIMIT;
    }
}