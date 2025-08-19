package com.quantum.batch.step;

import com.quantum.kis.model.KisMultiStockItem;
import com.quantum.kis.model.KisMultiStockResponse;
import com.quantum.kis.service.KisMultiStockPriceService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * KIS 멀티 주식 시세 수집 ItemProcessor
 * 
 * 30종목 배치를 받아서 KIS API로 멀티 조회 후 개별 종목 데이터로 변환
 * Rate Limiting과 에러 처리가 자동으로 적용됨
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisMultiStockPriceItemProcessor implements ItemProcessor<List<String>, List<KisMultiStockItem>> {

    private final KisMultiStockPriceService kisMultiStockPriceService;

    @Override
    public List<KisMultiStockItem> process(List<String> stockCodes) throws Exception {
        
        if (stockCodes == null || stockCodes.isEmpty()) {
            log.warn("KIS Multi Processor: Empty stock codes batch received");
            return new ArrayList<>();
        }

        log.info("KIS Multi Processor: Processing batch with {} stock codes: {}", 
                 stockCodes.size(), stockCodes);

        try {
            // 1. KIS 멀티 조회 API 호출 (최대 30종목 한번에)
            KisMultiStockResponse response = kisMultiStockPriceService.getMultiStockPrices(stockCodes);
            
            if (!response.isSuccess()) {
                log.error("KIS Multi Processor: API call failed - Code: {}, Message: {}", 
                          response.resultCode(), response.message());
                return new ArrayList<>();
            }

            // 2. 응답 데이터 검증
            List<KisMultiStockItem> stockItems = response.output();
            if (stockItems == null || stockItems.isEmpty()) {
                log.warn("KIS Multi Processor: No data returned for batch: {}", stockCodes);
                return new ArrayList<>();
            }

            // 3. 결과 로깅
            log.info("KIS Multi Processor: Successfully processed {} stocks, got {} items", 
                     stockCodes.size(), stockItems.size());

            // 4. 개별 종목별 상세 로깅 (DEBUG 레벨)
            stockItems.forEach(item -> {
                log.debug("KIS Multi Processor: {} ({}) - 현재가: {}, 등락: {} ({}%)", 
                          item.koreanName(), 
                          item.stockCode(),
                          item.currentPrice(),
                          item.priceChange(),
                          item.changeRate());
            });

            // 5. 거래 불가능한 종목 필터링 (선택적)
            List<KisMultiStockItem> tradableItems = stockItems.stream()
                .filter(item -> {
                    if (!item.isTradeable()) {
                        log.warn("KIS Multi Processor: {} ({}) is not tradeable - status: {}", 
                                 item.koreanName(), item.stockCode(), item.statusCode());
                        return false;
                    }
                    return true;
                })
                .toList();

            log.info("KIS Multi Processor: Filtered to {} tradeable items out of {}", 
                     tradableItems.size(), stockItems.size());

            return tradableItems;

        } catch (Exception e) {
            log.error("KIS Multi Processor: Failed to process stock batch: {}", stockCodes, e);
            
            // Rate Limiting 오류인 경우 특별 처리
            if (e.getMessage() != null && e.getMessage().contains("rate limit")) {
                log.warn("KIS Multi Processor: Rate limit exceeded, will retry later");
            }
            
            // 예외를 다시 던지지 않고 빈 리스트 반환 (배치 계속 진행)
            return new ArrayList<>();
        }
    }

    /**
     * 처리 성공률 계산 (모니터링용)
     */
    private double calculateSuccessRate(List<String> requested, List<KisMultiStockItem> processed) {
        if (requested.isEmpty()) {
            return 0.0;
        }
        return (double) processed.size() / requested.size() * 100.0;
    }
}