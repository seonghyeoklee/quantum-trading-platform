package com.quantum.kis.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;

/** KIS API 주식 현재가 조회 응답 모델 TR_ID: FHKST01010100 */
public record KisCurrentPriceResponse(
        @JsonProperty("rt_cd") String resultCode,
        @JsonProperty("msg_cd") String messageCode,
        @JsonProperty("msg1") String message,
        @JsonProperty("output") Output output) {

    public record Output(
            @JsonProperty("iscd_stat_cls_code") String stockStatusCode,
            @JsonProperty("marg_rate") String marginRate,
            @JsonProperty("rprs_mrkt_kor_name") String representativeMarketName,
            @JsonProperty("new_hgpr_lwpr_cls_code") String newHighLowClassCode,
            @JsonProperty("bstp_kor_isnm") String stockKoreanName,
            @JsonProperty("temp_stop_yn") String temporaryStopYn,
            @JsonProperty("oprc_rang_cont_yn") String openPriceRangeContinueYn,
            @JsonProperty("clpr_rang_cont_yn") String closePriceRangeContinueYn,
            @JsonProperty("crdt_able_yn") String creditAvailableYn,
            @JsonProperty("grmn_rate_cls_code") String guaranteeRateClassCode,
            @JsonProperty("elw_pblc_yn") String elwPublicYn,
            @JsonProperty("stck_prpr") String currentPrice,
            @JsonProperty("prdy_vrss") String previousDayComparison,
            @JsonProperty("prdy_vrss_sign") String previousDayComparisonSign,
            @JsonProperty("prdy_ctrt") String previousDayChangeRate,
            @JsonProperty("acml_tr_pbmn") String accumulatedTransactionAmount,
            @JsonProperty("acml_vol") String accumulatedVolume,
            @JsonProperty("prdy_vrss_vol_rate") String previousVolumeComparisonRate,
            @JsonProperty("stck_oprc") String openPrice,
            @JsonProperty("stck_hgpr") String highPrice,
            @JsonProperty("stck_lwpr") String lowPrice,
            @JsonProperty("stck_mxpr") String maxPrice,
            @JsonProperty("stck_llam") String minPrice,
            @JsonProperty("stck_sdpr") String standardPrice,
            @JsonProperty("wghn_avrg_stck_prc") String weightedAveragePrice,
            @JsonProperty("hts_frgn_ehrt") String foreignerHoldingRate,
            @JsonProperty("frgn_ntby_qty") String foreignerNetBuyQuantity,
            @JsonProperty("pgtr_ntby_qty") String programNetBuyQuantity,
            @JsonProperty("pvt_scnd_dmrs_prc") String pivotSecondResistancePrice,
            @JsonProperty("pvt_frst_dmrs_prc") String pivotFirstResistancePrice,
            @JsonProperty("pvt_pont_val") String pivotPointValue,
            @JsonProperty("pvt_frst_dmsp_prc") String pivotFirstSupportPrice,
            @JsonProperty("pvt_scnd_dmsp_prc") String pivotSecondSupportPrice,
            @JsonProperty("dmrs_val") String resistanceValue,
            @JsonProperty("dmsp_val") String supportValue,
            @JsonProperty("cpfn") String capitalFund,
            @JsonProperty("rstc_wdth_prc") String restrictionWidthPrice,
            @JsonProperty("stck_fcam") String stockFaceAmount,
            @JsonProperty("stck_sspr") String stockSuspendPrice,
            @JsonProperty("aspr_unit") String askPriceUnit,
            @JsonProperty("hts_deal_qty_unit_val") String htsDealQuantityUnitValue,
            @JsonProperty("lstn_stcn") String listedStockCount,
            @JsonProperty("hts_avls") String htsMarketCap,
            @JsonProperty("per") String per,
            @JsonProperty("pbr") String pbr,
            @JsonProperty("stac_month") String settlementMonth,
            @JsonProperty("vol_tnrt") String volumeTurnoverRate,
            @JsonProperty("eps") String eps,
            @JsonProperty("bps") String bps,
            @JsonProperty("d250_hgpr") String day250HighPrice,
            @JsonProperty("d250_hgpr_date") String day250HighPriceDate,
            @JsonProperty("d250_hgpr_vrss_prpr_rate") String day250HighPriceVsCurrentRate,
            @JsonProperty("d250_lwpr") String day250LowPrice,
            @JsonProperty("d250_lwpr_date") String day250LowPriceDate,
            @JsonProperty("d250_lwpr_vrss_prpr_rate") String day250LowPriceVsCurrentRate,
            @JsonProperty("stck_dryy_hgpr") String yearHighPrice,
            @JsonProperty("dryy_hgpr_vrss_prpr_rate") String yearHighPriceVsCurrentRate,
            @JsonProperty("dryy_hgpr_date") String yearHighPriceDate,
            @JsonProperty("stck_dryy_lwpr") String yearLowPrice,
            @JsonProperty("dryy_lwpr_vrss_prpr_rate") String yearLowPriceVsCurrentRate,
            @JsonProperty("dryy_lwpr_date") String yearLowPriceDate,
            @JsonProperty("w52_hgpr") String week52HighPrice,
            @JsonProperty("w52_hgpr_vrss_prpr_ctrt") String week52HighPriceVsCurrentRate,
            @JsonProperty("w52_hgpr_date") String week52HighPriceDate,
            @JsonProperty("w52_lwpr") String week52LowPrice,
            @JsonProperty("w52_lwpr_vrss_prpr_ctrt") String week52LowPriceVsCurrentRate,
            @JsonProperty("w52_lwpr_date") String week52LowPriceDate,
            @JsonProperty("whol_loan_rmnd_rate") String wholeLoanRemainRate,
            @JsonProperty("ssts_yn") String shortSellingAvailableYn,
            @JsonProperty("stck_shrn_iscd") String stockShortCode,
            @JsonProperty("fcam_cnnm") String faceAmountCurrencyName,
            @JsonProperty("cpfn_cnnm") String capitalFundCurrencyName,
            @JsonProperty("apprch_rate") String approachRate,
            @JsonProperty("frgn_hldn_qty") String foreignerHoldingQuantity,
            @JsonProperty("vi_cls_code") String viClassCode,
            @JsonProperty("ovtm_vi_cls_code") String overtimeViClassCode,
            @JsonProperty("last_ssts_cntg_qty") String lastShortSellingQuantity,
            @JsonProperty("invt_caful_yn") String investmentCautionYn,
            @JsonProperty("mrkt_warn_cls_code") String marketWarningClassCode,
            @JsonProperty("short_over_yn") String shortOverheatingYn,
            @JsonProperty("sltr_yn") String settlementTradingYn,
            @JsonProperty("mang_issu_cls_code") String managementIssueClassCode) {

        /** 현재가를 BigDecimal로 변환 */
        public BigDecimal getCurrentPriceAsBigDecimal() {
            try {
                return new BigDecimal(currentPrice);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }

        /** 전일 대비 변화율을 BigDecimal로 변환 */
        public BigDecimal getPreviousChangeRateAsBigDecimal() {
            try {
                return new BigDecimal(previousDayChangeRate);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }

        /** 거래량을 Long으로 변환 */
        public Long getAccumulatedVolumeAsLong() {
            try {
                return Long.parseLong(accumulatedVolume);
            } catch (NumberFormatException e) {
                return 0L;
            }
        }

        /** 시가를 BigDecimal로 변환 */
        public BigDecimal getOpenPriceAsBigDecimal() {
            try {
                return new BigDecimal(openPrice);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }

        /** 고가를 BigDecimal로 변환 */
        public BigDecimal getHighPriceAsBigDecimal() {
            try {
                return new BigDecimal(highPrice);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }

        /** 저가를 BigDecimal로 변환 */
        public BigDecimal getLowPriceAsBigDecimal() {
            try {
                return new BigDecimal(lowPrice);
            } catch (NumberFormatException e) {
                return BigDecimal.ZERO;
            }
        }
    }
}
