package com.quantum.core.domain.model.common;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * 시간 프레임 코드 열거형  
 * 캔들 차트의 시간 단위를 타입 안전하게 관리
 */
@Getter
@RequiredArgsConstructor
public enum TimeframeCode {

    ONE_MINUTE("1m", "1분봉", 1),
    FIVE_MINUTE("5m", "5분봉", 5),
    FIFTEEN_MINUTE("15m", "15분봉", 15),
    THIRTY_MINUTE("30m", "30분봉", 30),
    ONE_HOUR("1h", "시간봉", 60),
    FOUR_HOUR("4h", "4시간봉", 240),
    ONE_DAY("1d", "일봉", 1440),
    ONE_WEEK("1w", "주봉", 10080),
    ONE_MONTH("1M", "월봉", 43200);

    private final String code;
    private final String koreanName;
    private final int minutesValue;

    public static TimeframeCode fromCode(String code) {
        if (code == null || code.trim().isEmpty()) {
            return ONE_DAY; // 기본값
        }
        
        for (TimeframeCode timeframe : values()) {
            if (timeframe.code.equalsIgnoreCase(code.trim())) {
                return timeframe;
            }
        }
        
        throw new IllegalArgumentException("지원하지 않는 시간프레임 코드: " + code);
    }

    public boolean isIntraday() {
        return minutesValue < 1440; // 하루(1440분) 미만
    }

    public boolean isDaily() {
        return this == ONE_DAY;
    }

    public boolean isWeeklyOrMonthly() {
        return this == ONE_WEEK || this == ONE_MONTH;
    }
}