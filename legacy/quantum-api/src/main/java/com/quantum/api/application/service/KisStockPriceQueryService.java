package com.quantum.api.application.service;

import com.quantum.api.application.port.out.KisStockPriceCommandPort;
import com.quantum.api.application.port.out.KisStockPriceQueryPort;
import com.quantum.api.application.usecase.KisStockPriceQueryUsecase;
import com.quantum.kis.model.KisCurrentPriceResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/** 주식 조회 서비스 - Port를 통한 외부 시스템 연동 */
@Slf4j
@Service
@RequiredArgsConstructor
public class KisStockPriceQueryService implements KisStockPriceQueryUsecase {

    private final KisStockPriceQueryPort kisStockPriceQueryPort;
    private final KisStockPriceCommandPort kisStockPriceCommandPort;

    @Override
    public KisCurrentPriceResponse getCurrentPriceAndSave(String symbol) {
        log.info("Getting current price from KIS and saving for stock: {}", symbol);

        try {
            // 1. KIS API에서 원본 데이터 조회
            KisCurrentPriceResponse response =
                    kisStockPriceQueryPort.getCurrentPriceFromKis(symbol);
            log.info("Successfully retrieved KIS data for {}", symbol);

            // 2. 원본 데이터 그대로 저장 (분석용)
            kisStockPriceCommandPort.saveKisData(symbol, response);
            log.debug("KIS raw data saved for analysis: {}", symbol);

            return response;
        } catch (Exception e) {
            log.error("Failed to get and save KIS data for stock: {}", symbol, e);
            throw new RuntimeException("KIS 데이터 조회 및 저장 실패: " + symbol, e);
        }
    }
}
