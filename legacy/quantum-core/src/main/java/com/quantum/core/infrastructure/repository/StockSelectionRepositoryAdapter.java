package com.quantum.core.infrastructure.repository;

import com.quantum.core.domain.port.repository.StockSelectionRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Repository;

import java.util.Arrays;
import java.util.List;

/**
 * 주식 종목 선택 리포지토리 어댑터
 * 
 * 도메인 포트를 구현하여 실제 종목 데이터를 제공한다.
 * 현재는 하드코딩되어 있지만, 향후 DB나 외부 설정에서 가져올 수 있다.
 */
@Slf4j
@Repository
public class StockSelectionRepositoryAdapter implements StockSelectionRepository {
    
    /**
     * KOSPI 주요 종목 리스트
     * 향후 DB 테이블(tb_stock_selection)이나 설정 파일에서 관리할 수 있다.
     */
    private static final List<String> MAJOR_STOCKS = Arrays.asList(
            // 대형주 1군
            "005930", // 삼성전자
            "000660", // SK하이닉스  
            "035420", // NAVER
            "051910", // LG화학
            "006400", // 삼성SDI
            "035720", // 카카오
            "207940", // 삼성바이오로직스
            "068270", // 셀트리온
            "028260", // 삼성물산
            "066570", // LG전자
            
            // 대형주 2군
            "323410", // 카카오뱅크
            "373220", // LG에너지솔루션
            "000270", // 기아
            "012330", // 현대모비스
            "003670", // 포스코홀딩스
            "096770", // SK이노베이션
            "030200", // KT
            "017670", // SK텔레콤
            "034730", // SK
            "018260", // 삼성에스디에스
            
            // 중형주 포함
            "009150", // 삼성전기
            "010950", // S-Oil
            "086790", // 하나금융지주
            "316140", // 우리금융지주
            "105560", // KB금융
            "055550", // 신한지주
            "032830", // 삼성생명
            "004020", // 현대제철
            "000720", // 현대건설
            "011200"  // HMM
    );
    
    @Override
    public List<String> findMajorStocks() {
        log.debug("Finding major stocks: {} stocks", MAJOR_STOCKS.size());
        return MAJOR_STOCKS;
    }
    
    @Override
    public List<String> findMonitoringStocks() {
        // 현재는 주요 종목과 동일, 향후 별도 관리 가능
        return findMajorStocks();
    }
    
    @Override
    public List<String> findActiveStocks() {
        // 현재는 주요 종목과 동일, 향후 거래량 기반 동적 선택 가능
        return findMajorStocks();
    }
    
    @Override
    public boolean isMajorStock(String symbol) {
        return MAJOR_STOCKS.contains(symbol);
    }
}