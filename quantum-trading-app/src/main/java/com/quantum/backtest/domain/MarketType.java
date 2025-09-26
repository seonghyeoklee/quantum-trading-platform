package com.quantum.backtest.domain;

/**
 * 시장 구분 열거형
 * 국내주식과 해외주식을 구분하기 위한 타입
 */
public enum MarketType {

    DOMESTIC("국내"),
    OVERSEAS("해외");

    private final String displayName;

    MarketType(String displayName) {
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }

    /**
     * 종목코드를 보고 시장 구분을 자동 판별한다.
     * @param stockCode 종목코드
     * @return 시장 구분 (국내: 6자리 숫자, 해외: 문자 포함)
     */
    public static MarketType detectMarketType(String stockCode) {
        if (stockCode == null || stockCode.isBlank()) {
            return DOMESTIC; // 기본값
        }

        // 국내주식: 6자리 숫자 패턴
        if (stockCode.matches("^\\d{6}$")) {
            return DOMESTIC;
        }

        // 해외주식: 영문자 포함 패턴 (예: AAPL, TSLA)
        if (stockCode.matches("^[A-Za-z]{1,5}$")) {
            return OVERSEAS;
        }

        // 기타: 기본값
        return DOMESTIC;
    }

    /**
     * 국내주식인지 확인
     */
    public boolean isDomestic() {
        return this == DOMESTIC;
    }

    /**
     * 해외주식인지 확인
     */
    public boolean isOverseas() {
        return this == OVERSEAS;
    }
}