package com.quantum.api.adapter.out.stock;

import com.quantum.api.adapter.out.authentication.AuthenticationAdapter;
import com.quantum.api.application.port.out.KisStockPriceQueryPort;
import com.quantum.kis.client.KisFeignClient;
import com.quantum.kis.model.KisCurrentPriceResponse;
import com.quantum.kis.model.enums.KisCustomerType;
import com.quantum.kis.model.enums.KisMarketDivisionCode;
import com.quantum.kis.model.enums.KisTransactionId;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** KIS 주식 가격 데이터 조회 어댑터 (Query) CQRS 패턴 적용 - 조회 전용 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisStockPriceQueryAdapter implements KisStockPriceQueryPort {

    private final KisFeignClient kisFeignClient;
    private final AuthenticationAdapter authenticationAdapter;

    @Value("${kis.api.app-key}")
    private String appKey;

    @Value("${kis.api.app-secret}")
    private String appSecret;

    @Override
    public KisCurrentPriceResponse getCurrentPriceFromKis(String symbol) {
        log.debug("KIS: Getting current price from KIS for stock: {}", symbol);

        try {
            String validAccessToken = authenticationAdapter.getValidAccessToken();

            KisCurrentPriceResponse response =
                    kisFeignClient.getCurrentPrice(
                            KisMarketDivisionCode.KRX.getCode(),
                            symbol,
                            "Bearer " + validAccessToken,
                            appKey,
                            appSecret,
                            KisTransactionId.CURRENT_PRICE.getCode(),
                            KisCustomerType.PERSONAL.getCode());

            log.debug("KIS: Retrieved raw response for {}: {}", symbol, response.resultCode());
            return response;

        } catch (Exception e) {
            log.error("KIS: Failed to get current price from KIS for stock: {}", symbol, e);
            throw new RuntimeException("KIS API 조회 실패", e);
        }
    }
}
