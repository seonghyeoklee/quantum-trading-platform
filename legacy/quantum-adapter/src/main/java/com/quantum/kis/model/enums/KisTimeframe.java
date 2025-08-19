package com.quantum.kis.model.enums;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * KIS API 전용 시간프레임 열거형
 *
 * <p>quantum-core의 TimeframeCode와 분리하여 어댑터 계층의 독립성 확보
 */
@Getter
@RequiredArgsConstructor
public enum KisTimeframe {

    // 분봉
    MINUTE_1("1", "1분봉"),
    MINUTE_5("5", "5분봉"),
    MINUTE_15("15", "15분봉"),
    MINUTE_30("30", "30분봉"),
    MINUTE_60("60", "60분봉"),

    // 일/주/월봉
    DAILY("D", "일봉"),
    WEEKLY("W", "주봉"),
    MONTHLY("M", "월봉");

    private final String kisCode; // KIS API에서 사용하는 코드
    private final String description; // 설명

    /** KIS API 코드로부터 변환 */
    public static KisTimeframe fromKisCode(String kisCode) {
        if (kisCode == null || kisCode.trim().isEmpty()) {
            return DAILY; // 기본값
        }

        for (KisTimeframe timeframe : values()) {
            if (timeframe.kisCode.equalsIgnoreCase(kisCode.trim())) {
                return timeframe;
            }
        }

        throw new IllegalArgumentException("지원하지 않는 KIS 시간프레임 코드: " + kisCode);
    }

    /** 분봉 여부 */
    public boolean isIntraday() {
        return this != DAILY && this != WEEKLY && this != MONTHLY;
    }

    /** 일봉 여부 */
    public boolean isDaily() {
        return this == DAILY;
    }

    /** 주/월봉 여부 */
    public boolean isWeeklyOrMonthly() {
        return this == WEEKLY || this == MONTHLY;
    }

    /** KIS API TR ID 반환 */
    public String getTrId(boolean isProduction) {
        String prefix = isProduction ? "FHKST" : "FHKST"; // sandbox/production 동일

        return switch (this) {
            case MINUTE_1, MINUTE_5, MINUTE_15, MINUTE_30, MINUTE_60 -> prefix + "03010200"; // 분봉
            case DAILY -> prefix + "03010100"; // 일봉
            case WEEKLY -> prefix + "03010300"; // 주봉
            case MONTHLY -> prefix + "03010400"; // 월봉
        };
    }
}
