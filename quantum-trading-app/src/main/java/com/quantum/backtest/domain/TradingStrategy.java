package com.quantum.backtest.domain;

/**
 * 거래 전략 타입
 */
public enum TradingStrategy {
    BUY_AND_HOLD("매수 후 보유", "단순히 매수 후 기간 만료까지 보유"),
    MOVING_AVERAGE_CROSSOVER("이동평균 교차", "단기/장기 이동평균 교차 신호"),
    RSI_STRATEGY("RSI 전략", "RSI 과매수/과매도 구간 활용"),
    BOLLINGER_BANDS("볼린저 밴드", "볼린저 밴드 상하한선 돌파 전략"),
    DINO_SCORE_STRATEGY("DINO 점수 전략", "DINO 분석 점수 기반 매매");

    private final String displayName;
    private final String description;

    TradingStrategy(String displayName, String description) {
        this.displayName = displayName;
        this.description = description;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getDescription() {
        return description;
    }

    /**
     * 전략이 기술적 분석을 사용하는지 확인
     */
    public boolean usesTechnicalAnalysis() {
        return this == MOVING_AVERAGE_CROSSOVER ||
               this == RSI_STRATEGY ||
               this == BOLLINGER_BANDS;
    }

    /**
     * 전략이 펀더멘털 분석을 사용하는지 확인
     */
    public boolean usesFundamentalAnalysis() {
        return this == DINO_SCORE_STRATEGY;
    }
}