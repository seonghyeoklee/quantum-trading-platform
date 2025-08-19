package com.quantum.core.domain.port.repository;

import java.util.List;

/**
 * 주식 종목 선택 리포지토리 포트
 * 
 * 배치 처리나 모니터링을 위한 종목 선택 로직을 제공한다.
 * 이는 도메인 관심사로, 인프라스트럭처가 아닌 도메인이 결정한다.
 */
public interface StockSelectionRepository {
    
    /**
     * 주요 종목 리스트를 조회한다.
     * 
     * @return 주요 종목 코드 리스트
     */
    List<String> findMajorStocks();
    
    /**
     * 모니터링 대상 종목 리스트를 조회한다.
     * 
     * @return 모니터링 대상 종목 코드 리스트
     */
    List<String> findMonitoringStocks();
    
    /**
     * 활성 거래 종목 리스트를 조회한다.
     * 
     * @return 활성 거래 종목 코드 리스트
     */
    List<String> findActiveStocks();
    
    /**
     * 종목 코드로 주요 종목 여부를 확인한다.
     * 
     * @param symbol 종목 코드
     * @return 주요 종목 여부
     */
    boolean isMajorStock(String symbol);
}