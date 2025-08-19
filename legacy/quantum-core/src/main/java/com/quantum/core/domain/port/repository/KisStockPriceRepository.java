package com.quantum.core.domain.port.repository;

import com.quantum.core.domain.model.kis.KisStockPriceData;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * KIS 주식 가격 원본 데이터 리포지토리 포트
 */
public interface KisStockPriceRepository {

    /**
     * KIS 원본 데이터 저장
     */
    KisStockPriceData save(KisStockPriceData kisStockPriceData);

    /**
     * KIS 원본 데이터 일괄 저장
     */
    List<KisStockPriceData> saveAll(List<KisStockPriceData> kisStockPriceDataList);

    /**
     * 종목코드별 최신 데이터 조회
     */
    Optional<KisStockPriceData> findLatestBySymbol(String symbol);

    /**
     * 종목코드별 전체 히스토리 조회
     */
    List<KisStockPriceData> findBySymbolOrderByQueryTimeDesc(String symbol);

    /**
     * 종목코드별 기간별 히스토리 조회
     */
    List<KisStockPriceData> findBySymbolAndQueryTimeBetween(
            String symbol, LocalDateTime startTime, LocalDateTime endTime);

    /**
     * 모든 최신 종목 데이터 조회 (종목별 가장 최근 1건씩)
     */
    List<KisStockPriceData> findAllLatestBySymbol();

    /**
     * 전체 히스토리 조회 (시간순 정렬)
     */
    List<KisStockPriceData> findAllOrderByQueryTimeDesc();
}