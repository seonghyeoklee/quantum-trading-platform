package com.quantum.batch.step;

import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.NonTransientResourceException;
import org.springframework.batch.item.ParseException;
import org.springframework.batch.item.UnexpectedInputException;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.Iterator;
import java.util.List;

/**
 * KIS 주식 시세 수집 ItemReader
 * 주요 종목 리스트를 읽어서 처리 대상으로 제공
 */
@Slf4j
@Component
public class KisStockPriceItemReader implements ItemReader<String> {

    private Iterator<String> stockSymbolIterator;
    private boolean initialized = false;

    /**
     * 주요 종목 리스트 (KOSPI 대형주 중심)
     */
    private static final List<String> MAJOR_STOCKS = Arrays.asList(
            "005930", // 삼성전자
            "000660", // SK하이닉스
            "035420", // NAVER
            "051910", // LG화학
            "006400", // 삼성SDI
            "035720", // 카카오
            "207940", // 삼성바이오로직스
            "068270", // 셀트리온
            "028260", // 삼성물산
            "066570"  // LG전자
    );

    @Override
    public String read() throws Exception, UnexpectedInputException, ParseException, NonTransientResourceException {
        
        if (!initialized) {
            stockSymbolIterator = MAJOR_STOCKS.iterator();
            initialized = true;
            log.info("KIS Batch: Initialized stock symbol reader with {} symbols", MAJOR_STOCKS.size());
        }

        if (stockSymbolIterator.hasNext()) {
            String symbol = stockSymbolIterator.next();
            log.debug("KIS Batch: Reading symbol: {}", symbol);
            return symbol;
        }

        log.info("KIS Batch: Finished reading all stock symbols");
        return null; // 더 이상 읽을 데이터가 없음
    }
}