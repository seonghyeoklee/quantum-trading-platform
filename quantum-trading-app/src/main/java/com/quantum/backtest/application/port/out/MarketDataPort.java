package com.quantum.backtest.application.port.out;

import com.quantum.backtest.domain.PriceData;

import java.time.LocalDate;
import java.util.List;

/**
 * 시장 데이터 조회 Port
 */
public interface MarketDataPort {

    /**
     * 주가 이력을 조회한다.
     * @param stockCode 종목코드 (예: "005930")
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 주가 데이터 리스트 (시간순 정렬)
     */
    List<PriceData> getPriceHistory(String stockCode, LocalDate startDate, LocalDate endDate);

    /**
     * 특정일의 주가 데이터를 조회한다.
     * @param stockCode 종목코드
     * @param date 조회일
     * @return 주가 데이터 (Optional)
     */
    PriceData getPriceData(String stockCode, LocalDate date);

    /**
     * 종목 정보를 검증한다.
     * @param stockCode 종목코드
     * @return 유효한 종목인지 여부
     */
    boolean isValidStock(String stockCode);

    /**
     * 종목명을 조회한다.
     * @param stockCode 종목코드
     * @return 종목명
     */
    String getStockName(String stockCode);
}