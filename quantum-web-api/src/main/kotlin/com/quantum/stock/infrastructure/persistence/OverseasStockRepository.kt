package com.quantum.stock.infrastructure.persistence

import com.quantum.stock.domain.OverseasStock
import com.quantum.stock.domain.OverseasExchange
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.time.LocalDateTime

/**
 * 해외주식종목 Repository
 * 
 * DDD 기반 해외 주식 종목 데이터 접근 레이어
 */
@Repository
interface OverseasStockRepository : JpaRepository<OverseasStock, Long> {
    
    /**
     * 심볼과 거래소로 조회
     */
    fun findBySymbolAndExchange(symbol: String, exchange: OverseasExchange): OverseasStock?
    
    /**
     * 심볼과 거래소로 조회 (활성 종목만)
     */
    fun findBySymbolAndExchangeAndIsActiveTrue(symbol: String, exchange: OverseasExchange): OverseasStock?
    
    /**
     * 활성 종목 전체 조회
     */
    fun findByIsActiveTrueOrderBySymbolAsc(): List<OverseasStock>
    
    /**
     * 활성 종목 페이징 조회
     */
    fun findByIsActiveTrue(pageable: Pageable): Page<OverseasStock>
    
    /**
     * 거래소별 활성 종목 조회
     */
    fun findByExchangeAndIsActiveTrueOrderBySymbolAsc(exchange: OverseasExchange): List<OverseasStock>
    
    /**
     * 거래소별 활성 종목 페이징 조회
     */
    fun findByExchangeAndIsActiveTrue(exchange: OverseasExchange, pageable: Pageable): Page<OverseasStock>
    
    /**
     * 영어 종목명으로 검색 (부분 일치, 활성 종목만)
     */
    fun findByStockNameEngContainingAndIsActiveTrueOrderByStockNameEngAsc(stockNameEng: String): List<OverseasStock>
    
    /**
     * 영어 종목명으로 검색 페이징 (부분 일치, 활성 종목만)
     */
    fun findByStockNameEngContainingAndIsActiveTrue(stockNameEng: String, pageable: Pageable): Page<OverseasStock>
    
    /**
     * 섹터별 활성 종목 조회
     */
    fun findBySectorCodeAndIsActiveTrueOrderBySymbolAsc(sectorCode: String): List<OverseasStock>
    
    /**
     * 여러 심볼로 일괄 조회 (활성 종목만)
     */
    fun findBySymbolInAndIsActiveTrueOrderBySymbolAsc(symbols: List<String>): List<OverseasStock>
    
    /**
     * 거래소별 여러 심볼 일괄 조회 (활성 종목만)
     */
    fun findBySymbolInAndExchangeAndIsActiveTrueOrderBySymbolAsc(
        symbols: List<String>, 
        exchange: OverseasExchange
    ): List<OverseasStock>
    
    /**
     * 심볼과 거래소 존재 여부 확인
     */
    fun existsBySymbolAndExchange(symbol: String, exchange: OverseasExchange): Boolean
    
    /**
     * 활성 심볼과 거래소 존재 여부 확인
     */
    fun existsBySymbolAndExchangeAndIsActiveTrue(symbol: String, exchange: OverseasExchange): Boolean
    
    /**
     * 거래소별 종목 수 카운트 (활성 종목만)
     */
    fun countByExchangeAndIsActiveTrue(exchange: OverseasExchange): Long
    
    /**
     * 전체 활성 종목 수 카운트
     */
    fun countByIsActiveTrue(): Long
    
    /**
     * 최근 업데이트된 종목들 조회
     */
    @Query("""
        SELECT o FROM OverseasStock o 
        WHERE o.isActive = true 
        AND o.updatedAt >= :since 
        ORDER BY o.updatedAt DESC
    """)
    fun findRecentlyUpdatedStocks(@Param("since") since: LocalDateTime): List<OverseasStock>
    
    /**
     * 거래소별 종목 통계 조회
     */
    @Query("""
        SELECT o.exchange as exchange, 
               COUNT(*) as totalCount,
               COUNT(CASE WHEN o.isActive = true THEN 1 END) as activeCount
        FROM OverseasStock o 
        GROUP BY o.exchange
    """)
    fun findExchangeStatistics(): List<ExchangeStatistics>
    
    /**
     * 국가별 종목 수 조회 (활성 종목만)
     */
    @Query("""
        SELECT o.countryCode as countryCode, COUNT(*) as count
        FROM OverseasStock o 
        WHERE o.isActive = true 
        GROUP BY o.countryCode 
        ORDER BY count DESC
    """)
    fun findCountryStatistics(): List<CountryStatistics>
    
    /**
     * 심볼 또는 영어 종목명으로 통합 검색 (활성 종목만)
     */
    @Query("""
        SELECT o FROM OverseasStock o 
        WHERE o.isActive = true 
        AND (UPPER(o.symbol) LIKE UPPER(CONCAT('%', :keyword, '%')) 
             OR UPPER(o.stockNameEng) LIKE UPPER(CONCAT('%', :keyword, '%'))
             OR (:keyword IS NOT NULL AND o.stockNameKor LIKE CONCAT('%', :keyword, '%')))
        ORDER BY 
            CASE WHEN UPPER(o.symbol) = UPPER(:keyword) THEN 1 ELSE 2 END,
            CASE WHEN UPPER(o.stockNameEng) = UPPER(:keyword) THEN 1 ELSE 2 END,
            o.symbol ASC
    """)
    fun searchByKeyword(@Param("keyword") keyword: String): List<OverseasStock>
    
    /**
     * 심볼 또는 종목명으로 통합 검색 페이징 (활성 종목만)
     */
    @Query("""
        SELECT o FROM OverseasStock o 
        WHERE o.isActive = true 
        AND (UPPER(o.symbol) LIKE UPPER(CONCAT('%', :keyword, '%')) 
             OR UPPER(o.stockNameEng) LIKE UPPER(CONCAT('%', :keyword, '%'))
             OR (:keyword IS NOT NULL AND o.stockNameKor LIKE CONCAT('%', :keyword, '%')))
        ORDER BY 
            CASE WHEN UPPER(o.symbol) = UPPER(:keyword) THEN 1 ELSE 2 END,
            CASE WHEN UPPER(o.stockNameEng) = UPPER(:keyword) THEN 1 ELSE 2 END,
            o.symbol ASC
    """)
    fun searchByKeyword(@Param("keyword") keyword: String, pageable: Pageable): Page<OverseasStock>
    
    /**
     * 인기 검색 종목 (상세정보가 많은 순)
     */
    @Query("""
        SELECT o FROM OverseasStock o 
        LEFT JOIN o.stockDetails od 
        WHERE o.isActive = true 
        GROUP BY o.id 
        ORDER BY COUNT(od.id) DESC
    """)
    fun findPopularStocks(pageable: Pageable): Page<OverseasStock>
}

/**
 * 거래소 통계 DTO
 */
interface ExchangeStatistics {
    val exchange: OverseasExchange
    val totalCount: Long
    val activeCount: Long
}

/**
 * 국가 통계 DTO
 */
interface CountryStatistics {
    val countryCode: String
    val count: Long
}