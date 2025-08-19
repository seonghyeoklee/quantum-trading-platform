package com.quantum.core.domain.model.common;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * 기술적 지표 타입 열거형
 * 차트 분석에 사용되는 다양한 기술적 지표들을 분류
 */
@Getter
@RequiredArgsConstructor
public enum TechnicalIndicatorType {

    // === 추세 지표 (Trend Indicators) ===
    MOVING_AVERAGE("MA", "이동평균", "TREND", "일정 기간 가격의 평균"),
    EMA("EMA", "지수이동평균", "TREND", "최근 가격에 더 높은 가중치"),
    BOLLINGER_BANDS("BB", "볼린저밴드", "TREND", "이동평균 + 표준편차 기반 밴드"),
    PARABOLIC_SAR("SAR", "패러볼릭SAR", "TREND", "추세 전환점 포착"),
    
    // === 모멘텀 지표 (Momentum Indicators) ===
    RSI("RSI", "상대강도지수", "MOMENTUM", "과매수/과매도 구간 판단"),
    STOCHASTIC("STOCH", "스토캐스틱", "MOMENTUM", "고점/저점 대비 현재가 위치"),
    MACD("MACD", "MACD", "MOMENTUM", "이동평균 수렴확산"),
    CCI("CCI", "상품채널지수", "MOMENTUM", "평균가격 대비 편차"),
    WILLIAMS_R("WILLIAMS_R", "윌리엄스%R", "MOMENTUM", "고저점 기준 현재가 비율"),
    
    // === 거래량 지표 (Volume Indicators) ===
    OBV("OBV", "거래량균형", "VOLUME", "거래량 누적 기반 추세"),
    VOLUME_MA("VOL_MA", "거래량이동평균", "VOLUME", "거래량의 이동평균"),
    VWAP("VWAP", "거래량가중평균가격", "VOLUME", "거래량으로 가중한 평균가격"),
    
    // === 변동성 지표 (Volatility Indicators) ===
    ATR("ATR", "평균실제범위", "VOLATILITY", "가격 변동성 측정"),
    STANDARD_DEVIATION("STDDEV", "표준편차", "VOLATILITY", "가격 분산 정도"),
    
    // === 지지/저항 지표 (Support/Resistance) ===
    PIVOT_POINTS("PIVOT", "피봇포인트", "SUPPORT_RESISTANCE", "지지/저항선 계산"),
    FIBONACCI("FIBONACCI", "피보나치", "SUPPORT_RESISTANCE", "되돌림/확장 수준"),
    
    // === 캔들 패턴 (Candlestick Patterns) ===
    DOJI("DOJI", "도지", "CANDLESTICK", "시종가 동일한 캔들"),
    HAMMER("HAMMER", "망치형", "CANDLESTICK", "긴 아래꼬리 캔들"),
    ENGULFING("ENGULFING", "포용형", "CANDLESTICK", "이전 캔들을 감싸는 패턴");

    private final String code;           // 지표 코드
    private final String koreanName;     // 한글명
    private final String category;       // 카테고리
    private final String description;    // 설명

    /**
     * 카테고리별 지표 목록 조회
     */
    public static TechnicalIndicatorType[] getByCategory(String category) {
        return java.util.Arrays.stream(values())
                .filter(indicator -> indicator.category.equals(category))
                .toArray(TechnicalIndicatorType[]::new);
    }

    /**
     * 추세 지표 여부
     */
    public boolean isTrendIndicator() {
        return "TREND".equals(category);
    }

    /**
     * 모멘텀 지표 여부
     */
    public boolean isMomentumIndicator() {
        return "MOMENTUM".equals(category);
    }

    /**
     * 거래량 지표 여부
     */
    public boolean isVolumeIndicator() {
        return "VOLUME".equals(category);
    }

    /**
     * 변동성 지표 여부
     */
    public boolean isVolatilityIndicator() {
        return "VOLATILITY".equals(category);
    }
}