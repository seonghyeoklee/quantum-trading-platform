package com.quantum.shared;

import java.time.LocalDate;

/**
 * 시장 데이터 서비스 인터페이스
 * 모듈 간 독립성을 위한 중립적인 시장 데이터 접근 인터페이스
 */
public interface MarketDataService {

    /**
     * 일별 차트 데이터 조회
     *
     * @param stockCode 종목코드
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 차트 데이터 응답
     */
    MarketDataDto.ChartResponse getDailyChartData(String stockCode, LocalDate startDate, LocalDate endDate);

    /**
     * 종목명 조회
     *
     * @param stockCode 종목코드
     * @return 종목명 (조회 실패 시 종목코드 반환)
     */
    String getStockName(String stockCode);

    /**
     * 종목 유효성 검증
     *
     * @param stockCode 종목코드
     * @return 유효성 여부
     */
    boolean isValidStock(String stockCode);
}