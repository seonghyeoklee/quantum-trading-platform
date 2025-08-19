package com.quantum.kis.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;

/**
 * KIS 멀티 주식 조회 개별 종목 시세 정보
 *
 * <p>intstock-multprice API의 output 배열 내 개별 종목 데이터
 */
public record KisMultiStockItem(
        // 기본 종목 정보
        @JsonProperty("inter_kor_isnm") String koreanName, // 종목 한글명
        @JsonProperty("inter_shrn_iscd") String stockCode, // 종목 코드
        @JsonProperty("inter_eng_isnm") String englishName, // 종목 영문명

        // 현재 시세 정보
        @JsonProperty("inter2_prpr") String currentPrice, // 현재가
        @JsonProperty("inter2_prdy_vrss") String priceChange, // 전일 대비
        @JsonProperty("inter2_prdy_vrss_sign")
                String changeSign, // 전일 대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
        @JsonProperty("inter2_prdy_ctrt") String changeRate, // 전일 대비율

        // 거래량 정보
        @JsonProperty("inter2_acml_vol") String accumulatedVolume, // 누적 거래량
        @JsonProperty("inter2_acml_tr_pbmn") String accumulatedAmount, // 누적 거래대금

        // 시가/고가/저가 정보
        @JsonProperty("inter2_oprc") String openPrice, // 시가
        @JsonProperty("inter2_hgpr") String highPrice, // 고가
        @JsonProperty("inter2_lwpr") String lowPrice, // 저가

        // 상한/하한가 정보
        @JsonProperty("inter2_uplmtprc") String upperLimitPrice, // 상한가
        @JsonProperty("inter2_lwlmtprc") String lowerLimitPrice, // 하한가

        // 호가 정보
        @JsonProperty("inter2_askp1") String askPrice1, // 매도호가1
        @JsonProperty("inter2_bidp1") String bidPrice1, // 매수호가1

        // 시장 정보
        @JsonProperty("inter2_mrkt_div_code") String marketDivCode, // 시장구분코드
        @JsonProperty("inter2_stat_cls_code") String statusCode // 종목상태코드 (51: 거래정지, 52: 거래중단 등)
        ) {

    /** 현재가를 BigDecimal로 변환 */
    public BigDecimal getCurrentPriceAsBigDecimal() {
        try {
            return new BigDecimal(currentPrice);
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }

    /** 전일 대비 금액을 BigDecimal로 변환 */
    public BigDecimal getPriceChangeAsBigDecimal() {
        try {
            return new BigDecimal(priceChange);
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }

    /** 전일 대비율을 BigDecimal로 변환 */
    public BigDecimal getChangeRateAsBigDecimal() {
        try {
            return new BigDecimal(changeRate);
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }

    /** 누적 거래량을 Long으로 변환 */
    public Long getAccumulatedVolumeAsLong() {
        try {
            return Long.parseLong(accumulatedVolume);
        } catch (NumberFormatException e) {
            return 0L;
        }
    }

    /** 상승/하락/보합 여부 확인 */
    public PriceChangeType getPriceChangeType() {
        return switch (changeSign) {
            case "1" -> PriceChangeType.UPPER_LIMIT; // 상한
            case "2" -> PriceChangeType.RISE; // 상승
            case "3" -> PriceChangeType.FLAT; // 보합
            case "4" -> PriceChangeType.LOWER_LIMIT; // 하한
            case "5" -> PriceChangeType.FALL; // 하락
            default -> PriceChangeType.UNKNOWN;
        };
    }

    /** 종목 거래 가능 여부 확인 (종목상태코드 기반) */
    public boolean isTradeable() {
        // 51: 거래정지, 52: 거래중단, 53: 투자주의, 54: 투자경고, 55: 투자위험
        return !"51".equals(statusCode) && !"52".equals(statusCode);
    }

    /** 고위험 종목 여부 확인 */
    public boolean isHighRisk() {
        // 53: 투자주의, 54: 투자경고, 55: 투자위험
        return "53".equals(statusCode) || "54".equals(statusCode) || "55".equals(statusCode);
    }

    /** 가격 변동 타입 열거형 */
    public enum PriceChangeType {
        UPPER_LIMIT, // 상한
        RISE, // 상승
        FLAT, // 보합
        LOWER_LIMIT, // 하한
        FALL, // 하락
        UNKNOWN // 알 수 없음
    }
}
