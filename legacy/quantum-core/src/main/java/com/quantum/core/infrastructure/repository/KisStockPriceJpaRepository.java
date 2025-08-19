package com.quantum.core.infrastructure.repository;

import com.quantum.core.domain.model.kis.KisStockPriceData;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * KIS 주식 가격 원본 데이터 JPA 리포지토리 (Spring Data JPA)
 */
public interface KisStockPriceJpaRepository extends JpaRepository<KisStockPriceData, Long> {

    /**
     * 종목코드별 최신 데이터 조회
     */
    @Query("SELECT k FROM KisStockPriceData k WHERE k.symbol = :symbol ORDER BY k.queryTime DESC LIMIT 1")
    Optional<KisStockPriceData> findLatestBySymbol(@Param("symbol") String symbol);

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
    @Query("""
        SELECT k FROM KisStockPriceData k 
        WHERE k.queryTime = (
            SELECT MAX(k2.queryTime) FROM KisStockPriceData k2 WHERE k2.symbol = k.symbol
        )
        ORDER BY k.symbol
        """)
    List<KisStockPriceData> findAllLatestBySymbol();

    /**
     * 전체 히스토리 조회 (시간순 정렬)
     */
    @Query("SELECT k FROM KisStockPriceData k ORDER BY k.queryTime DESC")
    List<KisStockPriceData> findAllOrderByQueryTimeDesc();
}