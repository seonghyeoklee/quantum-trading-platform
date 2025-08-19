package com.quantum.core.domain.model.kis;

import com.quantum.core.infrastructure.common.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

import java.time.LocalDateTime;

/**
 * KIS API 주식 핵심 가격 데이터 엔티티
 * 거래에 필요한 핵심 가격 정보만 포함
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
@Table(name = "tb_kis_stock_price")
public class KisStockPrice extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "symbol", nullable = false, length = 12)
    @Comment("종목코드")
    private String symbol;

    @Column(name = "rt_cd", length = 10)
    @Comment("성공 실패 여부")
    private String resultCode;

    @Column(name = "msg_cd", length = 10)
    @Comment("응답코드")
    private String messageCode;

    @Column(name = "msg1", length = 100)
    @Comment("응답메세지")
    private String message;

    @Column(name = "bstp_kor_isnm", length = 100)
    @Comment("업종 한글 종목명")
    private String stockKoreanName;

    @Column(name = "stck_prpr", length = 20)
    @Comment("주식 현재가")
    private String currentPrice;

    @Column(name = "prdy_vrss", length = 20)
    @Comment("전일 대비")
    private String previousDayComparison;

    @Column(name = "prdy_vrss_sign", length = 1)
    @Comment("전일 대비 부호")
    private String previousDayComparisonSign;

    @Column(name = "prdy_ctrt", length = 20)
    @Comment("전일 대비율")
    private String previousDayChangeRate;

    @Column(name = "acml_tr_pbmn", length = 30)
    @Comment("누적 거래 대금")
    private String accumulatedTransactionAmount;

    @Column(name = "acml_vol", length = 20)
    @Comment("누적 거래량")
    private String accumulatedVolume;

    @Column(name = "prdy_vrss_vol_rate", length = 20)
    @Comment("전일 대비 거래량 비율")
    private String previousVolumeComparisonRate;

    @Column(name = "stck_oprc", length = 20)
    @Comment("주식 시가")
    private String openPrice;

    @Column(name = "stck_hgpr", length = 20)
    @Comment("주식 최고가")
    private String highPrice;

    @Column(name = "stck_lwpr", length = 20)
    @Comment("주식 최저가")
    private String lowPrice;

    @Column(name = "stck_mxpr", length = 20)
    @Comment("주식 상한가")
    private String maxPrice;

    @Column(name = "stck_llam", length = 20)
    @Comment("주식 하한가")
    private String minPrice;

    @Column(name = "stck_sdpr", length = 20)
    @Comment("주식 기준가")
    private String standardPrice;

    @Column(name = "wghn_avrg_stck_prc", length = 20)
    @Comment("가중 평균 주식 가격")
    private String weightedAveragePrice;

    @Column(name = "query_time")
    @Comment("조회 시점")
    private LocalDateTime queryTime;

    @Builder
    public KisStockPrice(
            String symbol, String resultCode, String messageCode, String message,
            String stockKoreanName, String currentPrice, String previousDayComparison,
            String previousDayComparisonSign, String previousDayChangeRate,
            String accumulatedTransactionAmount, String accumulatedVolume,
            String previousVolumeComparisonRate, String openPrice, String highPrice,
            String lowPrice, String maxPrice, String minPrice, String standardPrice,
            String weightedAveragePrice) {

        this.symbol = symbol;
        this.resultCode = resultCode;
        this.messageCode = messageCode;
        this.message = message;
        this.stockKoreanName = stockKoreanName;
        this.currentPrice = currentPrice;
        this.previousDayComparison = previousDayComparison;
        this.previousDayComparisonSign = previousDayComparisonSign;
        this.previousDayChangeRate = previousDayChangeRate;
        this.accumulatedTransactionAmount = accumulatedTransactionAmount;
        this.accumulatedVolume = accumulatedVolume;
        this.previousVolumeComparisonRate = previousVolumeComparisonRate;
        this.openPrice = openPrice;
        this.highPrice = highPrice;
        this.lowPrice = lowPrice;
        this.maxPrice = maxPrice;
        this.minPrice = minPrice;
        this.standardPrice = standardPrice;
        this.weightedAveragePrice = weightedAveragePrice;
        this.queryTime = LocalDateTime.now();
    }

    /**
     * 종목 상태 구분 코드를 enum으로 변환
     */
    public StockStatusCode getStockStatus() {
        return StockStatusCode.fromCode(resultCode);
    }

    /**
     * 거래 가능 여부
     */
    public boolean isTradeable() {
        StockStatusCode status = getStockStatus();
        return status != null && status.isTradeable();
    }
}