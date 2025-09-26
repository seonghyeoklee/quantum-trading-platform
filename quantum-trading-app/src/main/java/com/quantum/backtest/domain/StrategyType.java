package com.quantum.backtest.domain;

/**
 * 거래 전략 타입
 */
public enum StrategyType {
    BUY_AND_HOLD("매수 후 보유", "단순히 매수 후 기간 만료까지 보유하는 전략"),
    MOVING_AVERAGE_CROSSOVER("이동평균 교차", "단기/장기 이동평균 교차 신호 기반 매매"),
    RSI_STRATEGY("RSI 전략", "RSI 과매수/과매도 구간을 활용한 매매"),
    BOLLINGER_BANDS("볼린저 밴드", "볼린저 밴드 상하한선 돌파를 활용한 매매"),
    DINO_SCORE_STRATEGY("DINO 점수 전략", "DINO 분석 점수 기반 종목 선택 매매"),
    MA_RSI_COMBO("이동평균+RSI 조합", "이동평균 교차와 RSI 신호를 결합한 하이브리드 전략");

    private final String displayName;
    private final String description;

    StrategyType(String displayName, String description) {
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
               this == BOLLINGER_BANDS ||
               this == MA_RSI_COMBO;
    }

    /**
     * 전략이 펀더멘털 분석을 사용하는지 확인
     */
    public boolean usesFundamentalAnalysis() {
        return this == DINO_SCORE_STRATEGY;
    }

    /**
     * 전략이 파라미터를 필요로 하는지 확인
     */
    public boolean requiresParameters() {
        return this != BUY_AND_HOLD;
    }
}