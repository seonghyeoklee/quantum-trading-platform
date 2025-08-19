package com.quantum.core.infrastructure.repository;

import com.quantum.core.domain.model.kis.KisRawDataStore;
import com.quantum.core.domain.port.repository.KisRawDataRepository;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * KIS 원본 JSON 데이터 JPA 리포지토리
 */
@Repository
public interface KisRawDataRepositoryImpl extends JpaRepository<KisRawDataStore, Long>, KisRawDataRepository {

    /**
     * 종목코드 + API 타입별 최신 데이터 조회
     */
    @Query("SELECT k FROM KisRawDataStore k WHERE k.symbol = :symbol AND k.apiType = :apiType ORDER BY k.queryTime DESC LIMIT 1")
    Optional<KisRawDataStore> findLatestBySymbolAndApiType(@Param("symbol") String symbol, @Param("apiType") String apiType);

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