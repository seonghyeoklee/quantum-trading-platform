package com.quantum.kis.client;

import com.quantum.kis.config.KisFeignConfig;
import com.quantum.kis.model.KisCurrentPriceResponse;
import com.quantum.kis.model.KisMultiStockResponse;
import com.quantum.kis.model.KisStockCandleResponse;
import com.quantum.kis.model.KisTokenResponse;
import java.util.Map;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestParam;

@FeignClient(
        name = "kis-api",
        url = "${kis.api.base-url:https://openapi.koreainvestment.com:9443}",
        configuration = KisFeignConfig.class)
public interface KisFeignClient {

    /** 인증 토큰 발급 공통 헤더는 인터셉터에서 자동 처리 */
    @PostMapping("/oauth2/tokenP")
    KisTokenResponse getAccessToken(@RequestBody Map<String, String> requestBody);

    /** 주식 현재가 조회 */
    @GetMapping("/uapi/domestic-stock/v1/quotations/inquire-price")
    KisCurrentPriceResponse getCurrentPrice(
            @RequestParam("FID_COND_MRKT_DIV_CODE") String marketDivCode,
            @RequestParam("FID_INPUT_ISCD") String stockCode,
            @RequestHeader("authorization") String authorization,
            @RequestHeader("appkey") String appkey,
            @RequestHeader("appsecret") String appsecret,
            @RequestHeader("tr_id") String trId,
            @RequestHeader("custtype") String custtype);

    /** 일봉 차트 데이터 조회 */
    @GetMapping("/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice")
    KisStockCandleResponse getDailyCandleData(
            @RequestParam("FID_COND_MRKT_DIV_CODE") String marketDivCode,
            @RequestParam("FID_INPUT_ISCD") String stockCode,
            @RequestParam("fid_input_date_1") String startDate,
            @RequestParam("fid_input_date_2") String endDate,
            @RequestParam("fid_period_div_code") String periodCode,
            @RequestParam("fid_org_adj_prc") String adjustedPrice,
            @RequestHeader("authorization") String authorization,
            @RequestHeader("tr_id") String trId);

    /** 분봉 차트 데이터 조회 */
    @GetMapping("/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice")
    KisStockCandleResponse getMinuteCandleData(
            @RequestParam("FID_COND_MRKT_DIV_CODE") String marketDivCode,
            @RequestParam("FID_INPUT_ISCD") String stockCode,
            @RequestParam("fid_input_hour_1") String inputDate,
            @RequestParam("fid_pw_data_incu_yn") String includeHistoricalData,
            @RequestParam("fid_period_div_code") String periodCode,
            @RequestHeader("authorization") String authorization,
            @RequestHeader("tr_id") String trId);

    /** 계좌 잔고 조회 */
    @GetMapping("/uapi/domestic-stock/v1/trading/inquire-balance")
    <T> T getAccountBalance(
            @RequestParam("CANO") String accountNo,
            @RequestParam("ACNT_PRDT_CD") String accountProductCode,
            @RequestParam("AFHR_FLPR_YN") String afterHoursFlagPrice,
            @RequestParam("OFL_YN") String overflowYn,
            @RequestParam("INQR_DVSN") String inquiryDivision,
            @RequestParam("UNPR_DVSN") String unitPriceDivision,
            @RequestParam("FUND_STTL_ICLD_YN") String fundSettlementInclude,
            @RequestParam("FNCG_AMT_AUTO_RDPT_YN") String financingAmountAutoRepayment,
            @RequestParam("PRCS_DVSN") String processDivision,
            @RequestParam("CTX_AREA_FK100") String contextAreaFk100,
            @RequestParam("CTX_AREA_NK100") String contextAreaNk100,
            @RequestHeader("authorization") String authorization,
            @RequestHeader("tr_id") String trId,
            Class<T> responseType);

    /** 관심종목(멀티종목) 시세조회 - 최대 30종목 한번에 조회 */
    @GetMapping("/uapi/domestic-stock/v1/quotations/intstock-multprice")
    KisMultiStockResponse getMultiStockPrice(
            @RequestParam
                    Map<String, String>
                            params, // 동적 파라미터 (FID_COND_MRKT_DIV_CODE_1~30, FID_INPUT_ISCD_1~30)
            @RequestHeader("authorization") String authorization,
            @RequestHeader("appkey") String appkey,
            @RequestHeader("appsecret") String appsecret,
            @RequestHeader("tr_id") String trId,
            @RequestHeader("custtype") String custtype);
}
