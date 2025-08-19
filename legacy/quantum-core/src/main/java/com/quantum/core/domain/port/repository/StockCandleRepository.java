package com.quantum.core.domain.port.repository;

import com.quantum.core.domain.model.StockCandle;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/** 주식 캔들 데이터 저장소 인터페이스 */
public interface StockCandleRepository {

    /** 캔들 데이터 저장 */
    StockCandle save(StockCandle candle);

    /** 캔들 데이터 배치 저장 (성능 최적화) */
    List<StockCandle> saveAll(List<StockCandle> candles);

    /** 특정 시점의 캔들 데이터 조회 */
    Optional<StockCandle> findBySymbolAndTimeframeAndTimestamp(
            String symbol, String timeframe, LocalDateTime timestamp);

    /** 심볼과 시간대별 캔들 데이터 조회 (기간 지정) */
    List<StockCandle> findBySymbolAndTimeframeBetween(
            String symbol, String timeframe, LocalDateTime startTime, LocalDateTime endTime);

    /** 심볼과 시간대별 최근 N개 캔들 데이터 조회 */
    List<StockCandle> findRecentCandles(String symbol, String timeframe, int limit);

    /** 마지막 캔들 데이터 조회 (배치 처리시 중복 방지용) */
    Optional<StockCandle> findLastCandle(String symbol, String timeframe);

    /** 특정 날짜의 모든 심볼 일봉 데이터 조회 */
    List<StockCandle> findDailyCandlesByDate(LocalDateTime date);

    /** 기간별 거래량 상위 종목 조회 */
    List<StockCandle> findTopVolumeStocks(
            String timeframe, LocalDateTime startTime, LocalDateTime endTime, int limit);

    /** 캔들 데이터 존재 여부 확인 */
    boolean existsBySymbolAndTimeframeAndTimestamp(
            String symbol, String timeframe, LocalDateTime timestamp);

    /** 오래된 캔들 데이터 삭제 (데이터 정리용) */
    void deleteOlderThan(LocalDateTime cutoffDate);

    /** 심볼별 캔들 데이터 개수 조회 */
    long countBySymbolAndTimeframe(String symbol, String timeframe);
}
