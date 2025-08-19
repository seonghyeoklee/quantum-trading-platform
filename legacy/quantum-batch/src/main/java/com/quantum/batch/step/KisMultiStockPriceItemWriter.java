package com.quantum.batch.step;

import com.quantum.core.domain.model.kis.KisStockPriceData;
import com.quantum.core.domain.port.repository.KisStockPriceRepository;
import com.quantum.kis.model.KisMultiStockItem;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.Chunk;
import org.springframework.batch.item.ItemWriter;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

/**
 * KIS 멀티 주식 시세 수집 ItemWriter
 * 
 * 멀티 조회로 받은 종목 데이터들을 DB에 저장
 * 개별 종목별로 KisStockPriceData 엔티티로 변환하여 저장
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisMultiStockPriceItemWriter implements ItemWriter<List<KisMultiStockItem>> {

    private final KisStockPriceRepository kisStockPriceRepository;

    @Override
    @Transactional
    public void write(Chunk<? extends List<KisMultiStockItem>> chunk) throws Exception {
        
        if (chunk.isEmpty()) {
            log.debug("KIS Multi Writer: Empty chunk received");
            return;
        }

        log.info("KIS Multi Writer: Processing chunk with {} batches", chunk.size());

        List<KisStockPriceData> allStockData = new ArrayList<>();
        int totalProcessed = 0;

        // 각 배치(List<KisMultiStockItem>)를 처리
        for (List<KisMultiStockItem> stockBatch : chunk) {
            if (stockBatch == null || stockBatch.isEmpty()) {
                continue;
            }

            log.debug("KIS Multi Writer: Processing batch with {} items", stockBatch.size());

            // 배치 내 각 종목을 KisStockPriceData로 변환
            for (KisMultiStockItem item : stockBatch) {
                try {
                    KisStockPriceData stockData = convertToStockPriceData(item);
                    allStockData.add(stockData);
                    totalProcessed++;
                    
                    log.debug("KIS Multi Writer: Converted {} ({}) - Price: {}", 
                              item.koreanName(), item.stockCode(), item.currentPrice());
                              
                } catch (Exception e) {
                    log.error("KIS Multi Writer: Failed to convert item: {} ({})", 
                              item.koreanName(), item.stockCode(), e);
                }
            }
        }

        // 일괄 저장
        if (!allStockData.isEmpty()) {
            try {
                kisStockPriceRepository.saveAll(allStockData);
                log.info("KIS Multi Writer: Successfully saved {} stock price records", totalProcessed);
                
                // 저장된 종목 리스트 로깅 (INFO 레벨)
                allStockData.forEach(data -> {
                    log.info("KIS Multi Writer: Saved {} - {}: {} 원", 
                             data.getSymbol(), 
                             data.getStockKoreanName(), 
                             data.getCurrentPrice());
                });
                
            } catch (Exception e) {
                log.error("KIS Multi Writer: Failed to save {} stock price records", allStockData.size(), e);
                throw e; // 배치 실패로 처리
            }
        } else {
            log.warn("KIS Multi Writer: No valid stock data to save");
        }
    }

    /**
     * KisMultiStockItem을 KisStockPriceData로 변환
     */
    private KisStockPriceData convertToStockPriceData(KisMultiStockItem item) {
        return KisStockPriceData.builder()
                .symbol(item.stockCode())
                .stockKoreanName(item.koreanName())
                .currentPrice(item.currentPrice())
                .previousDayComparison(item.priceChange())
                .previousDayComparisonSign(item.changeSign())
                .previousDayChangeRate(item.changeRate())
                .accumulatedVolume(item.accumulatedVolume())
                .openPrice(item.openPrice())
                .highPrice(item.highPrice())
                .lowPrice(item.lowPrice())
                .maxPrice(item.upperLimitPrice())
                .minPrice(item.lowerLimitPrice())
                .stockStatusCode(item.statusCode())
                .build();
    }

}