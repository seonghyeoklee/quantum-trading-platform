package com.quantum.core.domain.service;

import com.quantum.core.domain.port.repository.StockSelectionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * 주식 종목 선택 도메인 서비스
 * 
 * 배치 처리나 모니터링을 위한 종목 선택 비즈니스 로직을 담당한다.
 * 이는 순수한 도메인 로직으로 인프라스트럭처에 의존하지 않는다.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class StockSelectionService {
    
    private final StockSelectionRepository stockSelectionRepository;
    
    /**
     * 배치 처리를 위한 종목 리스트를 배치 크기로 분할한다.
     * 
     * @param batchSize 배치 크기
     * @return 배치 단위로 분할된 종목 리스트
     */
    public List<List<String>> createStockBatchesForProcessing(int batchSize) {
        List<String> majorStocks = stockSelectionRepository.findMajorStocks();
        return createBatches(majorStocks, batchSize);
    }
    
    /**
     * 모니터링을 위한 종목 리스트를 배치 크기로 분할한다.
     * 
     * @param batchSize 배치 크기
     * @return 배치 단위로 분할된 종목 리스트
     */
    public List<List<String>> createStockBatchesForMonitoring(int batchSize) {
        List<String> monitoringStocks = stockSelectionRepository.findMonitoringStocks();
        return createBatches(monitoringStocks, batchSize);
    }
    
    /**
     * 활성 거래 종목 리스트를 배치 크기로 분할한다.
     * 
     * @param batchSize 배치 크기
     * @return 배치 단위로 분할된 종목 리스트
     */
    public List<List<String>> createActiveStockBatches(int batchSize) {
        List<String> activeStocks = stockSelectionRepository.findActiveStocks();
        return createBatches(activeStocks, batchSize);
    }
    
    /**
     * 주요 종목 수를 반환한다.
     * 
     * @return 주요 종목 수
     */
    public int getMajorStockCount() {
        return stockSelectionRepository.findMajorStocks().size();
    }
    
    /**
     * 예상 배치 수를 계산한다.
     * 
     * @param batchSize 배치 크기
     * @return 예상 배치 수
     */
    public int getExpectedBatchCount(int batchSize) {
        int stockCount = getMajorStockCount();
        return (stockCount + batchSize - 1) / batchSize;
    }
    
    /**
     * 종목 리스트를 배치 크기로 분할한다.
     * 
     * @param stocks 종목 리스트
     * @param batchSize 배치 크기
     * @return 배치 단위로 분할된 종목 리스트
     */
    private List<List<String>> createBatches(List<String> stocks, int batchSize) {
        List<List<String>> batches = new ArrayList<>();
        
        for (int i = 0; i < stocks.size(); i += batchSize) {
            int endIndex = Math.min(i + batchSize, stocks.size());
            List<String> batch = new ArrayList<>(stocks.subList(i, endIndex));
            batches.add(batch);
            
            log.debug("Created batch {}: {} symbols (index {}-{})", 
                      batches.size(), batch.size(), i, endIndex - 1);
        }
        
        log.info("Created {} batches from {} stocks with batch size {}", 
                 batches.size(), stocks.size(), batchSize);
        
        return batches;
    }
}