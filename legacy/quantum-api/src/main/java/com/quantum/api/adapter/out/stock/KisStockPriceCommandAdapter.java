package com.quantum.api.adapter.out.stock;

import com.quantum.api.application.port.out.KisStockPriceCommandPort;
import com.quantum.api.infrastructure.mapper.KisDataMapper;
import com.quantum.core.domain.model.kis.KisRawDataStore;
import com.quantum.core.domain.model.kis.KisStockPriceData;
import com.quantum.core.domain.port.repository.KisRawDataRepository;
import com.quantum.core.domain.port.repository.KisStockPriceRepository;
import com.quantum.kis.model.KisCurrentPriceResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/** KIS 주식 가격 데이터 저장 어댑터 (Command) CQRS 패턴 적용 - 저장 전용 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisStockPriceCommandAdapter implements KisStockPriceCommandPort {

    private final KisStockPriceRepository kisStockPriceRepository;
    private final KisRawDataRepository kisRawDataRepository;
    private final KisDataMapper kisDataMapper;

    @Override
    public void saveKisData(String symbol, KisCurrentPriceResponse response) {
        log.debug("KIS: Saving raw data for stock: {}", symbol);

        try {
            // 1. 구조화된 데이터 저장 (MapStruct 자동 매핑)
            KisStockPriceData kisData = kisDataMapper.toEntity(symbol, response);
            kisStockPriceRepository.save(kisData);

            // 2. JSON 원본 백업 저장 (무제한 확장성)
            KisRawDataStore rawStore = kisDataMapper.toRawStore(symbol, response);
            kisRawDataRepository.save(rawStore);

            log.debug("KIS: Successfully saved both structured and raw data for {}", symbol);

        } catch (Exception e) {
            log.error("KIS: Failed to save raw data for stock: {}", symbol, e);
            throw new RuntimeException("KIS 원본 데이터 저장 실패", e);
        }
    }
}
