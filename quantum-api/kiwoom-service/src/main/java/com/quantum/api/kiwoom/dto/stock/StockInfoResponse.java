package com.quantum.api.kiwoom.dto.stock;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * 키움증권 주식 기본정보 응답 DTO
 * API: /api/dostk/stkinfo
 * api-id: ka10001
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "주식 기본정보 응답")
public class StockInfoResponse {
    
    // ========== 기본 정보 ==========
    @JsonProperty("stk_cd")
    @Schema(description = "종목코드", example = "005930")
    private String stockCode;
    
    @JsonProperty("stk_nm")
    @Schema(description = "종목명", example = "삼성전자")
    private String stockName;
    
    @JsonProperty("setl_mm")
    @Schema(description = "결산월", example = "12")
    private String settlementMonth;
    
    @JsonProperty("fav")
    @Schema(description = "액면가", example = "100")
    private String faceValue;
    
    @JsonProperty("cap")
    @Schema(description = "자본금", example = "897514000000")
    private String capital;
    
    @JsonProperty("flo_stk")
    @Schema(description = "상장주식", example = "5969782550")
    private String listedShares;
    
    // ========== 신용/대용 정보 ==========
    @JsonProperty("crd_rt")
    @Schema(description = "신용비율", example = "0.15")
    private String creditRatio;
    
    @JsonProperty("repl_pric")
    @Schema(description = "대용가", example = "52800")
    private String collateralPrice;
    
    // ========== 연중 최고/최저 ==========
    @JsonProperty("oyr_hgst")
    @Schema(description = "연중최고", example = "88800")
    private String yearHigh;
    
    @JsonProperty("oyr_lwst")
    @Schema(description = "연중최저", example = "53000")
    private String yearLow;
    
    // ========== 시가총액 정보 ==========
    @JsonProperty("mac")
    @Schema(description = "시가총액", example = "398245290275000")
    private String marketCap;
    
    @JsonProperty("mac_wght")
    @Schema(description = "시가총액비중", example = "30.5")
    private String marketCapWeight;
    
    @JsonProperty("for_exh_rt")
    @Schema(description = "외인소진률", example = "51.23")
    private String foreignExhaustionRate;
    
    // ========== 투자 지표 ==========
    @JsonProperty("per")
    @Schema(description = "PER (주가수익비율)", example = "13.2")
    private String per;
    
    @JsonProperty("eps")
    @Schema(description = "EPS (주당순이익)", example = "5077")
    private String eps;
    
    @JsonProperty("roe")
    @Schema(description = "ROE (자기자본이익률)", example = "8.9")
    private String roe;
    
    @JsonProperty("pbr")
    @Schema(description = "PBR (주가순자산비율)", example = "1.15")
    private String pbr;
    
    @JsonProperty("ev")
    @Schema(description = "EV (기업가치)", example = "450000000000000")
    private String ev;
    
    @JsonProperty("bps")
    @Schema(description = "BPS (주당순자산)", example = "58123")
    private String bps;
    
    // ========== 재무 정보 ==========
    @JsonProperty("sale_amt")
    @Schema(description = "매출액", example = "279600000000000")
    private String salesAmount;
    
    @JsonProperty("bus_pro")
    @Schema(description = "영업이익", example = "35850000000000")
    private String operatingProfit;
    
    @JsonProperty("cup_nga")
    @Schema(description = "당기순이익", example = "30230000000000")
    private String netIncome;
    
    // ========== 250일 최고/최저 ==========
    @JsonProperty("250hgst")
    @Schema(description = "250일최고", example = "88800")
    private String day250High;
    
    @JsonProperty("250lwst")
    @Schema(description = "250일최저", example = "53000")
    private String day250Low;
    
    @JsonProperty("250hgst_pric_dt")
    @Schema(description = "250일최고가일", example = "20240115")
    private String day250HighDate;
    
    @JsonProperty("250hgst_pric_pre_rt")
    @Schema(description = "250일최고가대비율", example = "-15.32")
    private String day250HighRatio;
    
    @JsonProperty("250lwst_pric_dt")
    @Schema(description = "250일최저가일", example = "20231026")
    private String day250LowDate;
    
    @JsonProperty("250lwst_pric_pre_rt")
    @Schema(description = "250일최저가대비율", example = "35.85")
    private String day250LowRatio;
    
    // ========== 현재가 정보 ==========
    @JsonProperty("cur_prc")
    @Schema(description = "현재가", example = "71900")
    private String currentPrice;
    
    @JsonProperty("pre_sig")
    @Schema(description = "대비기호", example = "2")
    private String changeSign;
    
    @JsonProperty("pred_pre")
    @Schema(description = "전일대비", example = "-800")
    private String priceChange;
    
    @JsonProperty("flu_rt")
    @Schema(description = "등락율", example = "-1.10")
    private String changeRate;
    
    // ========== 당일 가격 정보 ==========
    @JsonProperty("high_pric")
    @Schema(description = "고가", example = "72900")
    private String highPrice;
    
    @JsonProperty("open_pric")
    @Schema(description = "시가", example = "72700")
    private String openPrice;
    
    @JsonProperty("low_pric")
    @Schema(description = "저가", example = "71800")
    private String lowPrice;
    
    @JsonProperty("upl_pric")
    @Schema(description = "상한가", example = "93600")
    private String upperLimitPrice;
    
    @JsonProperty("lst_pric")
    @Schema(description = "하한가", example = "50700")
    private String lowerLimitPrice;
    
    @JsonProperty("base_pric")
    @Schema(description = "기준가", example = "72700")
    private String basePrice;
    
    // ========== 예상 체결 정보 ==========
    @JsonProperty("exp_cntr_pric")
    @Schema(description = "예상체결가", example = "71900")
    private String expectedPrice;
    
    @JsonProperty("exp_cntr_qty")
    @Schema(description = "예상체결수량", example = "125000")
    private String expectedVolume;
    
    // ========== 거래량 정보 ==========
    @JsonProperty("trde_qty")
    @Schema(description = "거래량", example = "15234567")
    private String tradingVolume;
    
    @JsonProperty("trde_pre")
    @Schema(description = "거래대비", example = "85.23")
    private String tradingChangeRatio;
    
    // ========== 유통 정보 ==========
    @JsonProperty("fav_unit")
    @Schema(description = "액면가단위", example = "원")
    private String faceValueUnit;
    
    @JsonProperty("dstr_stk")
    @Schema(description = "유통주식", example = "4523456789")
    private String floatingShares;
    
    @JsonProperty("dstr_rt")
    @Schema(description = "유통비율", example = "75.81")
    private String floatingRatio;
    
    // ========== 유틸리티 메서드 ==========
    
    /**
     * 현재가를 BigDecimal로 변환
     */
    public BigDecimal getCurrentPriceAsDecimal() {
        try {
            return currentPrice != null ? new BigDecimal(currentPrice) : BigDecimal.ZERO;
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }
    
    /**
     * 등락율을 Double로 변환
     */
    public Double getChangeRateAsDouble() {
        try {
            return changeRate != null ? Double.parseDouble(changeRate) : 0.0;
        } catch (NumberFormatException e) {
            return 0.0;
        }
    }
    
    /**
     * 거래량을 Long으로 변환
     */
    public Long getTradingVolumeAsLong() {
        try {
            return tradingVolume != null ? Long.parseLong(tradingVolume) : 0L;
        } catch (NumberFormatException e) {
            return 0L;
        }
    }
    
    /**
     * 상승/하락 여부 판단
     */
    public boolean isRising() {
        return "1".equals(changeSign) || "2".equals(changeSign);
    }
    
    /**
     * 하락 여부 판단
     */
    public boolean isFalling() {
        return "4".equals(changeSign) || "5".equals(changeSign);
    }
    
    /**
     * 보합 여부 판단
     */
    public boolean isUnchanged() {
        return "3".equals(changeSign);
    }
}