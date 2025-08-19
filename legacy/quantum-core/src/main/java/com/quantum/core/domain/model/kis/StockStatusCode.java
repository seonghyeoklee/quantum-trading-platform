package com.quantum.core.domain.model.kis;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * 종목 상태 구분 코드 (iscd_stat_cls_code)
 * KIS API 응답에서 제공되는 종목의 거래 상태 정보
 */
@Getter
@RequiredArgsConstructor
public enum StockStatusCode {

    MANAGEMENT_STOCK("51", "관리종목"),
    INVESTMENT_RISK("52", "투자위험"),
    INVESTMENT_WARNING("53", "투자경고"),
    INVESTMENT_CAUTION("54", "투자주의"),
    CREDIT_AVAILABLE("55", "신용가능"),
    MARGIN_100_PERCENT("57", "증거금 100%"),
    TRADING_HALT("58", "거래정지"),
    SHORT_TERM_OVERHEATING("59", "단기과열종목");

    private final String code;
    private final String description;

    /**
     * 코드값으로 enum 찾기
     */
    public static StockStatusCode fromCode(String code) {
        if (code == null || code.isEmpty()) {
            return null;
        }
        
        for (StockStatusCode status : values()) {
            if (status.code.equals(code)) {
                return status;
            }
        }
        
        return null;
    }

    /**
     * 거래 가능 여부 판단
     */
    public boolean isTradeable() {
        return switch (this) {
            case CREDIT_AVAILABLE -> true;
            case INVESTMENT_CAUTION -> true;
            case MARGIN_100_PERCENT -> true;
            case MANAGEMENT_STOCK,
                 INVESTMENT_RISK,
                 INVESTMENT_WARNING,
                 TRADING_HALT,
                 SHORT_TERM_OVERHEATING -> false;
        };
    }

    /**
     * 고위험 종목 여부
     */
    public boolean isHighRisk() {
        return switch (this) {
            case INVESTMENT_RISK,
                 INVESTMENT_WARNING,
                 SHORT_TERM_OVERHEATING -> true;
            case MANAGEMENT_STOCK,
                 INVESTMENT_CAUTION,
                 CREDIT_AVAILABLE,
                 MARGIN_100_PERCENT,
                 TRADING_HALT -> false;
        };
    }
}