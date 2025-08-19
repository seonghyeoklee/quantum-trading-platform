package com.quantum.core.domain.port.repository;

import com.quantum.core.domain.model.kis.KisRawDataStore;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * KIS 원본 JSON 데이터 리포지토리 포트
 */
public interface KisRawDataRepository {

    /**
     * 원본 JSON 데이터 저장
     */
    KisRawDataStore save(KisRawDataStore rawData);

    /**
     * 종목코드 + API 타입별 최신 데이터 조회
     */
    Optional<KisRawDataStore> findLatestBySymbolAndApiType(String symbol, String apiType);

    /**
     * 종목코드별 전체 JSON 히스토리 조회
     */
    List<KisRawDataStore> findBySymbolOrderByQueryTimeDesc(String symbol);

    /**
     * API 타입별 전체 데이터 조회
     */
    List<KisRawDataStore> findByApiTypeOrderByQueryTimeDesc(String apiType);

    /**
     * 기간별 JSON 데이터 조회
     */
    List<KisRawDataStore> findBySymbolAndApiTypeAndQueryTimeBetween(
            String symbol, String apiType, LocalDateTime startTime, LocalDateTime endTime);
}