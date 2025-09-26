package com.quantum.kis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * KIS 일봉차트 조회 응답 DTO
 * TR_ID: FHKST03010100 (국내주식기간별시세)
 */
public record ChartDataResponse(
        @JsonProperty("rt_cd") String returnCode,          // 성공실패 여부 (0: 성공, 그외 실패)
        @JsonProperty("msg_cd") String messageCode,        // 응답코드
        @JsonProperty("msg1") String message,              // 응답메세지
        @JsonProperty("output1") Output1 output1,          // 응답상세1 (종목정보)
        @JsonProperty("output2") List<Output2> output2     // 응답상세2 (차트데이터)
) {

    /**
     * 종목 정보
     */
    public record Output1(
            @JsonProperty("prdy_vrss") String prdyVrss,    // 전일대비
            @JsonProperty("prdy_vrss_sign") String prdyVrssSign, // 전일대비부호
            @JsonProperty("prdy_ctrt") String prdyCtrt,    // 전일대비율
            @JsonProperty("stck_prdy_clpr") String stckPrdyClpr, // 주식전일종가
            @JsonProperty("acml_vol") String acmlVol,      // 누적거래량
            @JsonProperty("acml_tr_pbmn") String acmlTrPbmn, // 누적거래대금
            @JsonProperty("hts_kor_isnm") String htsKorIsnm,  // HTS한글종목명
            @JsonProperty("stck_prpr") String stckPrpr     // 주식현재가
    ) {}

    /**
     * 일봉 차트 데이터 (OHLCV)
     */
    public record Output2(
            @JsonProperty("stck_bsop_date") String stckBsopDate, // 주식영업일자 (YYYYMMDD)
            @JsonProperty("stck_clpr") String stckClpr,     // 주식종가 (종가)
            @JsonProperty("stck_oprc") String stckOprc,     // 주식시가 (시가)
            @JsonProperty("stck_hgpr") String stckHgpr,     // 주식최고가 (고가)
            @JsonProperty("stck_lwpr") String stckLwpr,     // 주식최저가 (저가)
            @JsonProperty("acml_vol") String acmlVol,       // 누적거래량 (거래량)
            @JsonProperty("acml_tr_pbmn") String acmlTrPbmn, // 누적거래대금
            @JsonProperty("flng_cls_code") String flngClsCode, // 락구분코드
            @JsonProperty("prtt_rate") String prttRate,     // 분할비율
            @JsonProperty("mod_yn") String modYn,           // 분할변경여부
            @JsonProperty("prdy_vrss_sign") String prdyVrssSign, // 전일대비부호
            @JsonProperty("prdy_vrss") String prdyVrss,     // 전일대비
            @JsonProperty("revl_issu_reas") String revlIssuReas  // 재평가사유코드
    ) {}

    /**
     * 성공 응답인지 확인
     */
    public boolean isSuccess() {
        return "0".equals(returnCode);
    }
}