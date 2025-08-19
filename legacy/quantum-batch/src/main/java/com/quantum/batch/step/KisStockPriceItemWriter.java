package com.quantum.batch.step;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.Chunk;
import org.springframework.batch.item.ItemWriter;
import org.springframework.stereotype.Component;

/**
 * KIS 주식 시세 수집 ItemWriter
 * 처리된 종목 정보를 로깅 (실제 저장은 Processor에서 이미 완료)
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisStockPriceItemWriter implements ItemWriter<String> {

    @Override
    public void write(Chunk<? extends String> chunk) throws Exception {
        
        if (chunk.isEmpty()) {
            log.debug("KIS Batch: No items to write in this chunk");
            return;
        }

        log.info("KIS Batch: Successfully processed {} stock symbols in chunk", chunk.size());
        
        for (String stockSymbol : chunk) {
            log.debug("KIS Batch: Successfully wrote data for symbol: {}", stockSymbol);
        }
        
        log.info("KIS Batch: Chunk write completed - {} symbols processed", chunk.size());
    }
}