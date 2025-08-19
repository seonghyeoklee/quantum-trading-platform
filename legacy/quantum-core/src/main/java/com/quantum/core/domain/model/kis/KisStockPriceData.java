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
 * KIS API 주식 현재가 원본 데이터 저장 엔티티
 * (분석용 - 76개 모든 필드 보존)
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
@Table(name = "tb_kis_stock_price_data")
public class KisStockPriceData extends BaseTimeEntity {

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

    // === Output 필드들 ===
    @Column(name = "iscd_stat_cls_code", length = 10)
    @Comment("종목 상태 구분 코드")
    private String stockStatusCode;

    @Column(name = "marg_rate", length = 20)
    @Comment("증거금 비율")
    private String marginRate;

    @Column(name = "rprs_mrkt_kor_name", length = 50)
    @Comment("대표 시장 한글 명")
    private String representativeMarketName;

    @Column(name = "new_hgpr_lwpr_cls_code", length = 10)
    @Comment("신 고가 저가 구분 코드")
    private String newHighLowClassCode;

    @Column(name = "bstp_kor_isnm", length = 100)
    @Comment("업종 한글 종목명")
    private String stockKoreanName;

    @Column(name = "temp_stop_yn", length = 1)
    @Comment("임시 정지 여부")
    private String temporaryStopYn;

    @Column(name = "oprc_rang_cont_yn", length = 1)
    @Comment("시가 범위 연장 여부")
    private String openPriceRangeContinueYn;

    @Column(name = "clpr_rang_cont_yn", length = 1)
    @Comment("종가 범위 연장 여부")
    private String closePriceRangeContinueYn;

    @Column(name = "crdt_able_yn", length = 1)
    @Comment("신용 가능 여부")
    private String creditAvailableYn;

    @Column(name = "grmn_rate_cls_code", length = 10)
    @Comment("보증금 비율 구분 코드")
    private String guaranteeRateClassCode;

    @Column(name = "elw_pblc_yn", length = 1)
    @Comment("ELW 발행 여부")
    private String elwPublicYn;

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

    @Column(name = "hts_frgn_ehrt", length = 20)
    @Comment("HTS 외국인 소진율")
    private String foreignerHoldingRate;

    @Column(name = "frgn_ntby_qty", length = 20)
    @Comment("외국인 순매수 수량")
    private String foreignerNetBuyQuantity;

    @Column(name = "pgtr_ntby_qty", length = 20)
    @Comment("프로그램매매 순매수 수량")
    private String programNetBuyQuantity;

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

    @Column(name = "cpfn", length = 30)
    @Comment("자본금")
    private String capitalFund;

    @Column(name = "rstc_wdth_prc", length = 20)
    @Comment("제한 폭 가격")
    private String restrictionWidthPrice;

    @Column(name = "stck_fcam", length = 20)
    @Comment("주식 액면가")
    private String stockFaceAmount;

    @Column(name = "stck_sspr", length = 20)
    @Comment("주식 대용가")
    private String stockSuspendPrice;

    @Column(name = "aspr_unit", length = 10)
    @Comment("호가단위")
    private String askPriceUnit;

    @Column(name = "hts_deal_qty_unit_val", length = 20)
    @Comment("HTS 매매 수량 단위 값")
    private String htsDealQuantityUnitValue;

    @Column(name = "lstn_stcn", length = 30)
    @Comment("상장 주수")
    private String listedStockCount;

    @Column(name = "hts_avls", length = 30)
    @Comment("HTS 시가총액")
    private String htsMarketCap;

    @Column(name = "per", length = 20)
    @Comment("PER")
    private String per;

    @Column(name = "pbr", length = 20)
    @Comment("PBR")
    private String pbr;

    @Column(name = "stac_month", length = 2)
    @Comment("결산 월")
    private String settlementMonth;

    @Column(name = "vol_tnrt", length = 20)
    @Comment("거래량 회전율")
    private String volumeTurnoverRate;

    @Column(name = "eps", length = 20)
    @Comment("EPS")
    private String eps;

    @Column(name = "bps", length = 20)
    @Comment("BPS")
    private String bps;

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

    @Column(name = "whol_loan_rmnd_rate", length = 20)
    @Comment("전체 융자 잔고 비율")
    private String wholeLoanRemainRate;

    @Column(name = "ssts_yn", length = 1)
    @Comment("공매도가능여부")
    private String shortSellingAvailableYn;

    @Column(name = "stck_shrn_iscd", length = 12)
    @Comment("주식 단축 종목코드")
    private String stockShortCode;

    @Column(name = "fcam_cnnm", length = 10)
    @Comment("액면가 통화명")
    private String faceAmountCurrencyName;

    @Column(name = "cpfn_cnnm", length = 10)
    @Comment("자본금 통화명")
    private String capitalFundCurrencyName;

    @Column(name = "apprch_rate", length = 20)
    @Comment("접근도")
    private String approachRate;

    @Column(name = "frgn_hldn_qty", length = 20)
    @Comment("외국인 보유 수량")
    private String foreignerHoldingQuantity;

    @Column(name = "vi_cls_code", length = 10)
    @Comment("VI적용구분코드")
    private String viClassCode;

    @Column(name = "ovtm_vi_cls_code", length = 10)
    @Comment("시간외단일가VI적용구분코드")
    private String overtimeViClassCode;

    @Column(name = "last_ssts_cntg_qty", length = 20)
    @Comment("최종 공매도 체결 수량")
    private String lastShortSellingQuantity;

    @Column(name = "invt_caful_yn", length = 1)
    @Comment("투자유의여부")
    private String investmentCautionYn;

    @Column(name = "mrkt_warn_cls_code", length = 10)
    @Comment("시장경고코드")
    private String marketWarningClassCode;

    @Column(name = "short_over_yn", length = 1)
    @Comment("단기과열여부")
    private String shortOverheatingYn;

    @Column(name = "sltr_yn", length = 1)
    @Comment("정리매매여부")
    private String settlementTradingYn;

    @Column(name = "mang_issu_cls_code", length = 10)
    @Comment("관리종목여부")
    private String managementIssueClassCode;

    @Column(name = "query_time")
    @Comment("조회 시점")
    private LocalDateTime queryTime;

    @Builder
    public KisStockPriceData(
            String symbol, String resultCode, String messageCode, String message,
            String stockStatusCode, String marginRate, String representativeMarketName,
            String newHighLowClassCode, String stockKoreanName, String temporaryStopYn,
            String openPriceRangeContinueYn, String closePriceRangeContinueYn,
            String creditAvailableYn, String guaranteeRateClassCode, String elwPublicYn,
            String currentPrice, String previousDayComparison, String previousDayComparisonSign,
            String previousDayChangeRate, String accumulatedTransactionAmount,
            String accumulatedVolume, String previousVolumeComparisonRate,
            String openPrice, String highPrice, String lowPrice, String maxPrice,
            String minPrice, String standardPrice, String weightedAveragePrice,
            String foreignerHoldingRate, String foreignerNetBuyQuantity,
            String programNetBuyQuantity, String pivotSecondResistancePrice,
            String pivotFirstResistancePrice, String pivotPointValue,
            String pivotFirstSupportPrice, String pivotSecondSupportPrice,
            String resistanceValue, String supportValue, String capitalFund,
            String restrictionWidthPrice, String stockFaceAmount, String stockSuspendPrice,
            String askPriceUnit, String htsDealQuantityUnitValue, String listedStockCount,
            String htsMarketCap, String per, String pbr, String settlementMonth,
            String volumeTurnoverRate, String eps, String bps, String day250HighPrice,
            String day250HighPriceDate, String day250HighPriceVsCurrentRate,
            String day250LowPrice, String day250LowPriceDate, String day250LowPriceVsCurrentRate,
            String yearHighPrice, String yearHighPriceVsCurrentRate, String yearHighPriceDate,
            String yearLowPrice, String yearLowPriceVsCurrentRate, String yearLowPriceDate,
            String week52HighPrice, String week52HighPriceVsCurrentRate, String week52HighPriceDate,
            String week52LowPrice, String week52LowPriceVsCurrentRate, String week52LowPriceDate,
            String wholeLoanRemainRate, String shortSellingAvailableYn, String stockShortCode,
            String faceAmountCurrencyName, String capitalFundCurrencyName, String approachRate,
            String foreignerHoldingQuantity, String viClassCode, String overtimeViClassCode,
            String lastShortSellingQuantity, String investmentCautionYn,
            String marketWarningClassCode, String shortOverheatingYn,
            String settlementTradingYn, String managementIssueClassCode) {

        this.symbol = symbol;
        this.resultCode = resultCode;
        this.messageCode = messageCode;
        this.message = message;
        this.stockStatusCode = stockStatusCode;
        this.marginRate = marginRate;
        this.representativeMarketName = representativeMarketName;
        this.newHighLowClassCode = newHighLowClassCode;
        this.stockKoreanName = stockKoreanName;
        this.temporaryStopYn = temporaryStopYn;
        this.openPriceRangeContinueYn = openPriceRangeContinueYn;
        this.closePriceRangeContinueYn = closePriceRangeContinueYn;
        this.creditAvailableYn = creditAvailableYn;
        this.guaranteeRateClassCode = guaranteeRateClassCode;
        this.elwPublicYn = elwPublicYn;
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
        this.foreignerHoldingRate = foreignerHoldingRate;
        this.foreignerNetBuyQuantity = foreignerNetBuyQuantity;
        this.programNetBuyQuantity = programNetBuyQuantity;
        this.pivotSecondResistancePrice = pivotSecondResistancePrice;
        this.pivotFirstResistancePrice = pivotFirstResistancePrice;
        this.pivotPointValue = pivotPointValue;
        this.pivotFirstSupportPrice = pivotFirstSupportPrice;
        this.pivotSecondSupportPrice = pivotSecondSupportPrice;
        this.resistanceValue = resistanceValue;
        this.supportValue = supportValue;
        this.capitalFund = capitalFund;
        this.restrictionWidthPrice = restrictionWidthPrice;
        this.stockFaceAmount = stockFaceAmount;
        this.stockSuspendPrice = stockSuspendPrice;
        this.askPriceUnit = askPriceUnit;
        this.htsDealQuantityUnitValue = htsDealQuantityUnitValue;
        this.listedStockCount = listedStockCount;
        this.htsMarketCap = htsMarketCap;
        this.per = per;
        this.pbr = pbr;
        this.settlementMonth = settlementMonth;
        this.volumeTurnoverRate = volumeTurnoverRate;
        this.eps = eps;
        this.bps = bps;
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
        this.wholeLoanRemainRate = wholeLoanRemainRate;
        this.shortSellingAvailableYn = shortSellingAvailableYn;
        this.stockShortCode = stockShortCode;
        this.faceAmountCurrencyName = faceAmountCurrencyName;
        this.capitalFundCurrencyName = capitalFundCurrencyName;
        this.approachRate = approachRate;
        this.foreignerHoldingQuantity = foreignerHoldingQuantity;
        this.viClassCode = viClassCode;
        this.overtimeViClassCode = overtimeViClassCode;
        this.lastShortSellingQuantity = lastShortSellingQuantity;
        this.investmentCautionYn = investmentCautionYn;
        this.marketWarningClassCode = marketWarningClassCode;
        this.shortOverheatingYn = shortOverheatingYn;
        this.settlementTradingYn = settlementTradingYn;
        this.managementIssueClassCode = managementIssueClassCode;
        this.queryTime = LocalDateTime.now();
    }

    /**
     * 종목 상태 구분 코드를 enum으로 변환
     */
    public StockStatusCode getStockStatus() {
        return StockStatusCode.fromCode(stockStatusCode);
    }

    /**
     * 거래 가능 여부
     */
    public boolean isTradeable() {
        StockStatusCode status = getStockStatus();
        return status != null && status.isTradeable();
    }

    /**
     * 고위험 종목 여부
     */
    public boolean isHighRisk() {
        StockStatusCode status = getStockStatus();
        return status != null && status.isHighRisk();
    }
}