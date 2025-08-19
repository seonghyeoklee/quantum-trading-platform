package com.quantum.core.domain.model.kis;

import com.quantum.core.infrastructure.common.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

/**
 * KIS API 주식 기술적 분석 데이터 엔티티
 * 피벗, 저항/지지선, 52주 고저가 등 기술적 분석 정보
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
@Table(name = "tb_kis_stock_technical")
public class KisStockTechnical extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "symbol", nullable = false, length = 12)
    @Comment("종목코드")
    private String symbol;

    @Column(name = "pvt_scnd_dmrs_prc", length = 20)
    @Comment("피벗 2차 디저항 가격")
    private String pivotSecondResistancePrice;

    @Column(name = "pvt_frst_dmrs_prc", length = 20)
    @Comment("피벗 1차 디저항 가격")
    private String pivotFirstResistancePrice;

    @Column(name = "pvt_pont_val", length = 20)
    @Comment("피벗 포인트 값")
    private String pivotPointValue;

    @Column(name = "pvt_frst_dmsp_prc", length = 20)
    @Comment("피벗 1차 디지지 가격")
    private String pivotFirstSupportPrice;

    @Column(name = "pvt_scnd_dmsp_prc", length = 20)
    @Comment("피벗 2차 디지지 가격")
    private String pivotSecondSupportPrice;

    @Column(name = "dmrs_val", length = 20)
    @Comment("디저항 값")
    private String resistanceValue;

    @Column(name = "dmsp_val", length = 20)
    @Comment("디지지 값")
    private String supportValue;

    @Column(name = "d250_hgpr", length = 20)
    @Comment("250일 최고가")
    private String day250HighPrice;

    @Column(name = "d250_hgpr_date", length = 8)
    @Comment("250일 최고가 일자")
    private String day250HighPriceDate;

    @Column(name = "d250_hgpr_vrss_prpr_rate", length = 20)
    @Comment("250일 최고가 대비 현재가 비율")
    private String day250HighPriceVsCurrentRate;

    @Column(name = "d250_lwpr", length = 20)
    @Comment("250일 최저가")
    private String day250LowPrice;

    @Column(name = "d250_lwpr_date", length = 8)
    @Comment("250일 최저가 일자")
    private String day250LowPriceDate;

    @Column(name = "d250_lwpr_vrss_prpr_rate", length = 20)
    @Comment("250일 최저가 대비 현재가 비율")
    private String day250LowPriceVsCurrentRate;

    @Column(name = "stck_dryy_hgpr", length = 20)
    @Comment("주식 연중 최고가")
    private String yearHighPrice;

    @Column(name = "dryy_hgpr_vrss_prpr_rate", length = 20)
    @Comment("연중 최고가 대비 현재가 비율")
    private String yearHighPriceVsCurrentRate;

    @Column(name = "dryy_hgpr_date", length = 8)
    @Comment("연중 최고가 일자")
    private String yearHighPriceDate;

    @Column(name = "stck_dryy_lwpr", length = 20)
    @Comment("주식 연중 최저가")
    private String yearLowPrice;

    @Column(name = "dryy_lwpr_vrss_prpr_rate", length = 20)
    @Comment("연중 최저가 대비 현재가 비율")
    private String yearLowPriceVsCurrentRate;

    @Column(name = "dryy_lwpr_date", length = 8)
    @Comment("연중 최저가 일자")
    private String yearLowPriceDate;

    @Column(name = "w52_hgpr", length = 20)
    @Comment("52주일 최고가")
    private String week52HighPrice;

    @Column(name = "w52_hgpr_vrss_prpr_ctrt", length = 20)
    @Comment("52주일 최고가 대비 현재가 대비")
    private String week52HighPriceVsCurrentRate;

    @Column(name = "w52_hgpr_date", length = 8)
    @Comment("52주일 최고가 일자")
    private String week52HighPriceDate;

    @Column(name = "w52_lwpr", length = 20)
    @Comment("52주일 최저가")
    private String week52LowPrice;

    @Column(name = "w52_lwpr_vrss_prpr_ctrt", length = 20)
    @Comment("52주일 최저가 대비 현재가 대비")
    private String week52LowPriceVsCurrentRate;

    @Column(name = "w52_lwpr_date", length = 8)
    @Comment("52주일 최저가 일자")
    private String week52LowPriceDate;

    @Builder
    public KisStockTechnical(
            String symbol, String pivotSecondResistancePrice, String pivotFirstResistancePrice,
            String pivotPointValue, String pivotFirstSupportPrice, String pivotSecondSupportPrice,
            String resistanceValue, String supportValue, String day250HighPrice,
            String day250HighPriceDate, String day250HighPriceVsCurrentRate,
            String day250LowPrice, String day250LowPriceDate, String day250LowPriceVsCurrentRate,
            String yearHighPrice, String yearHighPriceVsCurrentRate, String yearHighPriceDate,
            String yearLowPrice, String yearLowPriceVsCurrentRate, String yearLowPriceDate,
            String week52HighPrice, String week52HighPriceVsCurrentRate, String week52HighPriceDate,
            String week52LowPrice, String week52LowPriceVsCurrentRate, String week52LowPriceDate) {

        this.symbol = symbol;
        this.pivotSecondResistancePrice = pivotSecondResistancePrice;
        this.pivotFirstResistancePrice = pivotFirstResistancePrice;
        this.pivotPointValue = pivotPointValue;
        this.pivotFirstSupportPrice = pivotFirstSupportPrice;
        this.pivotSecondSupportPrice = pivotSecondSupportPrice;
        this.resistanceValue = resistanceValue;
        this.supportValue = supportValue;
        this.day250HighPrice = day250HighPrice;
        this.day250HighPriceDate = day250HighPriceDate;
        this.day250HighPriceVsCurrentRate = day250HighPriceVsCurrentRate;
        this.day250LowPrice = day250LowPrice;
        this.day250LowPriceDate = day250LowPriceDate;
        this.day250LowPriceVsCurrentRate = day250LowPriceVsCurrentRate;
        this.yearHighPrice = yearHighPrice;
        this.yearHighPriceVsCurrentRate = yearHighPriceVsCurrentRate;
        this.yearHighPriceDate = yearHighPriceDate;
        this.yearLowPrice = yearLowPrice;
        this.yearLowPriceVsCurrentRate = yearLowPriceVsCurrentRate;
        this.yearLowPriceDate = yearLowPriceDate;
        this.week52HighPrice = week52HighPrice;
        this.week52HighPriceVsCurrentRate = week52HighPriceVsCurrentRate;
        this.week52HighPriceDate = week52HighPriceDate;
        this.week52LowPrice = week52LowPrice;
        this.week52LowPriceVsCurrentRate = week52LowPriceVsCurrentRate;
        this.week52LowPriceDate = week52LowPriceDate;
    }
}