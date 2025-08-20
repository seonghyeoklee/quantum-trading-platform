package com.quantum.api.kiwoom.dto.chart.common;

/**
 * 차트 시간 타입
 * 차트 데이터의 시간 단위 분류
 */
public enum TimeType {
    
    /**
     * 틱 단위 (초 단위 실시간)
     */
    TICK("틱", "cntr_tm"),
    
    /**
     * 분 단위 (1분~60분봉)
     */
    MINUTE("분봉", "cntr_tm"),
    
    /**
     * 일 단위 (일봉)
     */
    DAILY("일봉", "dt"),
    
    /**
     * 주 단위 (주봉)
     */
    WEEKLY("주봉", "dt"),
    
    /**
     * 년 단위 (년봉)
     */
    YEARLY("년봉", "dt"),
    
    /**
     * 분석 차트 (기관별, 매물대 등)
     */
    ANALYSIS("분석", "dt");
    
    private final String description;
    private final String timeFieldName;
    
    TimeType(String description, String timeFieldName) {
        this.description = description;
        this.timeFieldName = timeFieldName;
    }
    
    /**
     * 시간 타입 설명
     */
    public String getDescription() {
        return description;
    }
    
    /**
     * 시간 필드명 (JSON 응답에서 사용)
     * cntr_tm: 체결시간 (틱, 분봉)
     * dt: 일자 (일봉, 주봉, 년봉, 분석)
     */
    public String getTimeFieldName() {
        return timeFieldName;
    }
    
    /**
     * 실시간 타입 여부 (틱, 분봉)
     */
    public boolean isRealTime() {
        return this == TICK || this == MINUTE;
    }
    
    /**
     * 기간 타입 여부 (일봉, 주봉, 년봉)
     */
    public boolean isPeriodic() {
        return this == DAILY || this == WEEKLY || this == YEARLY;
    }
}