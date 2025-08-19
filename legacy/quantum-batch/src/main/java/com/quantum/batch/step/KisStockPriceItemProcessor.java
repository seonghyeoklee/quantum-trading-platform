package com.quantum.batch.step;

import com.quantum.batch.service.KisTokenService;
import com.quantum.kis.client.KisFeignClient;
import com.quantum.kis.model.KisCurrentPriceResponse;
import com.quantum.kis.model.enums.KisCustomerType;
import com.quantum.kis.model.enums.KisMarketDivisionCode;
import com.quantum.kis.model.enums.KisTransactionId;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * KIS 주식 시세 수집 ItemProcessor
 * 종목 코드를 받아서 KIS API로 현재가 조회 후 DB 저장
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisStockPriceItemProcessor implements ItemProcessor<String, String> {

    private final KisFeignClient kisFeignClient;
    private final KisTokenService kisTokenService;

    @Value("${kis.api.app-key}")
    private String appKey;

    @Value("${kis.api.app-secret}")
    private String appSecret;

    @Override
    public String process(String stockSymbol) throws Exception {
        log.debug("KIS Batch: Processing stock symbol: {}", stockSymbol);

        try {
            // 1. Rate Limiting 체크 (KIS API 초당 20건, 분당 1000건 제한)
            String apiEndpoint = "getCurrentPrice";
            if (!kisTokenService.checkRateLimit(apiEndpoint)) {
                log.warn("KIS Batch: Rate limit exceeded for symbol: {} - skipping", stockSymbol);
                return null; // Rate limit 초과시 스킵
            }

            // 2. KisTokenService를 통해 유효한 토큰 조회
            String validAccessToken = kisTokenService.getValidAccessToken();
            
            if (validAccessToken == null) {
                log.error("KIS Batch: Failed to get valid access token for symbol: {}", stockSymbol);
                return null;
            }

            // 3. KIS API에서 현재가 조회
            KisCurrentPriceResponse response = kisFeignClient.getCurrentPrice(
                    KisMarketDivisionCode.KRX.getCode(),
                    stockSymbol,
                    "Bearer " + validAccessToken,
                    appKey,
                    appSecret,
                    KisTransactionId.CURRENT_PRICE.getCode(),
                    KisCustomerType.PERSONAL.getCode());

            if (response == null || !"0".equals(response.resultCode())) {
                log.warn("KIS Batch: Failed to get price for symbol: {} - {}", stockSymbol,
                    response != null ? response.message() : "null response");
                return null; // null 반환시 Writer로 전달되지 않음
            }

            String currentPrice = response.output().currentPrice();
            log.debug("KIS Batch: Successfully processed symbol: {} - price: {}",
                stockSymbol, currentPrice);

            return stockSymbol; // 성공한 경우 종목 코드 반환

        } catch (Exception e) {
            log.error("KIS Batch: Error processing symbol: {}", stockSymbol, e);
            // 배치 처리에서는 예외 발생시 해당 아이템만 스킵하고 계속 진행
            return null;
        }
    }
}
