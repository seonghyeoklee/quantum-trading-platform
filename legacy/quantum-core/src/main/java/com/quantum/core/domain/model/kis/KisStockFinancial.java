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
 * KIS API 주식 재무 데이터 엔티티
 * PER, PBR, EPS, BPS, 시가총액 등 재무 분석 정보
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
@Table(name = "tb_kis_stock_financial")
public class KisStockFinancial extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "symbol", nullable = false, length = 12)
    @Comment("종목코드")
    private String symbol;

    @Column(name = "marg_rate", length = 20)
    @Comment("증거금 비율")
    private String marginRate;

    @Column(name = "cpfn", length = 30)
    @Comment("자본금")
    private String capitalFund;

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

    @Column(name = "hts_frgn_ehrt", length = 20)
    @Comment("HTS 외국인 소진율")
    private String foreignerHoldingRate;

    @Column(name = "frgn_ntby_qty", length = 20)
    @Comment("외국인 순매수 수량")
    private String foreignerNetBuyQuantity;

    @Column(name = "pgtr_ntby_qty", length = 20)
    @Comment("프로그램매매 순매수 수량")
    private String programNetBuyQuantity;

    @Column(name = "rstc_wdth_prc", length = 20)
    @Comment("제한 폭 가격")
    private String restrictionWidthPrice;

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
    public KisStockFinancial(
            String symbol, String marginRate, String capitalFund, String stockFaceAmount,
            String stockSuspendPrice, String askPriceUnit, String htsDealQuantityUnitValue,
            String listedStockCount, String htsMarketCap, String per, String pbr,
            String settlementMonth, String volumeTurnoverRate, String eps, String bps,
            String foreignerHoldingRate, String foreignerNetBuyQuantity, String programNetBuyQuantity,
            String restrictionWidthPrice, String wholeLoanRemainRate, String shortSellingAvailableYn,
            String stockShortCode, String faceAmountCurrencyName, String capitalFundCurrencyName,
            String approachRate, String foreignerHoldingQuantity, String viClassCode,
            String overtimeViClassCode, String lastShortSellingQuantity, String investmentCautionYn,
            String marketWarningClassCode, String shortOverheatingYn, String settlementTradingYn,
            String managementIssueClassCode) {

        this.symbol = symbol;
        this.marginRate = marginRate;
        this.capitalFund = capitalFund;
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
        this.foreignerHoldingRate = foreignerHoldingRate;
        this.foreignerNetBuyQuantity = foreignerNetBuyQuantity;
        this.programNetBuyQuantity = programNetBuyQuantity;
        this.restrictionWidthPrice = restrictionWidthPrice;
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
     * 고위험 투자상품 여부
     */
    public boolean isHighRiskInvestment() {
        return "Y".equals(investmentCautionYn) || 
               "Y".equals(shortOverheatingYn) ||
               "Y".equals(settlementTradingYn);
    }

    /**
     * 신용거래 가능 여부
     */
    public boolean isCreditTradeable() {
        return !"N".equals(shortSellingAvailableYn);
    }

    /**
     * 외국인 지분율이 높은 종목인지 (30% 이상)
     */
    public boolean isHighForeignOwnership() {
        try {
            double rate = Double.parseDouble(foreignerHoldingRate);
            return rate >= 30.0;
        } catch (NumberFormatException e) {
            return false;
        }
    }
}