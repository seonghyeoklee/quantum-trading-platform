package com.quantum.batch.step;

import com.quantum.core.domain.service.StockSelectionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.NonTransientResourceException;
import org.springframework.batch.item.ParseException;
import org.springframework.batch.item.UnexpectedInputException;
import org.springframework.stereotype.Component;

import java.util.Iterator;
import java.util.List;

/**
 * KIS 멀티 주식 시세 수집 ItemReader
 * 
 * 도메인 서비스를 통해 주요 종목들을 30개씩 묶어서 배치로 처리
 * 기존 1종목씩 처리 → 30종목씩 처리로 대폭 성능 향상
 * 
 * 헥사고날 아키텍처 원칙에 따라 비즈니스 로직은 도메인 서비스가 담당
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisMultiStockPriceItemReader implements ItemReader<List<String>> {

    private final StockSelectionService stockSelectionService;
    
    private Iterator<List<String>> stockBatchIterator;
    private boolean initialized = false;

    /**
     * 배치 크기 (KIS API 멀티 조회 최대 30종목)
     */
    private static final int BATCH_SIZE = 30;

    @Override
    public List<String> read() throws Exception, UnexpectedInputException, ParseException, NonTransientResourceException {
        
        if (!initialized) {
            List<List<String>> stockBatches = createStockBatches();
            stockBatchIterator = stockBatches.iterator();
            initialized = true;
            log.info("KIS Multi Batch: Initialized with {} stock symbols in {} batches", 
                     MAJOR_STOCKS.size(), stockBatches.size());
        }

        if (stockBatchIterator.hasNext()) {
            List<String> batch = stockBatchIterator.next();
            log.info("KIS Multi Batch: Reading batch with {} symbols: {}", 
                     batch.size(), batch);
            return batch;
        }

        log.info("KIS Multi Batch: Finished reading all stock batches");
        return null; // 더 이상 읽을 데이터가 없음
    }

    /**
     * 종목 리스트를 배치 크기(30개)로 분할
     */
    private List<List<String>> createStockBatches() {
        List<List<String>> batches = new ArrayList<>();
        
        for (int i = 0; i < MAJOR_STOCKS.size(); i += BATCH_SIZE) {
            int endIndex = Math.min(i + BATCH_SIZE, MAJOR_STOCKS.size());
            List<String> batch = new ArrayList<>(MAJOR_STOCKS.subList(i, endIndex));
            batches.add(batch);
            
            log.debug("Created batch {}: {} symbols (index {}-{})", 
                      batches.size(), batch.size(), i, endIndex - 1);
        }
        
        return batches;
    }

    /**
     * 전체 종목 수 반환 (모니터링용)
     */
    public static int getTotalStockCount() {
        return MAJOR_STOCKS.size();
    }

    /**
     * 예상 배치 수 반환 (모니터링용)
     */
    public static int getExpectedBatchCount() {
        return (MAJOR_STOCKS.size() + BATCH_SIZE - 1) / BATCH_SIZE;
    }

    /**
     * 배치 크기 반환 (모니터링용)
     */
    public static int getBatchSize() {
        return BATCH_SIZE;
    }
}