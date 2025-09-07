package com.quantum.stock.infrastructure.persistence

import com.quantum.stock.domain.DomesticStock
import com.quantum.stock.domain.DomesticMarketType
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.time.LocalDateTime

/**
 * 국내주식종목 Repository
 * 
 * DDD 기반 국내 주식 종목 데이터 접근 레이어
 */
@Repository
interface DomesticStockRepository : JpaRepository<DomesticStock, Long> {
    
    /**
     * 종목코드로 조회
     */
    fun findByStockCode(stockCode: String): DomesticStock?
    
    /**
     * 종목코드로 조회 (활성 종목만)
     */
    fun findByStockCodeAndIsActiveTrue(stockCode: String): DomesticStock?
    
    /**
     * 활성 종목 전체 조회
     */
    fun findByIsActiveTrueOrderByStockCodeAsc(): List<DomesticStock>
    
    /**
     * 활성 종목 페이징 조회
     */
    fun findByIsActiveTrue(pageable: Pageable): Page<DomesticStock>
    
    /**
     * 시장별 활성 종목 조회
     */
    fun findByMarketTypeAndIsActiveTrueOrderByStockCodeAsc(marketType: DomesticMarketType): List<DomesticStock>
    
    /**
     * 시장별 활성 종목 페이징 조회
     */
    fun findByMarketTypeAndIsActiveTrue(marketType: DomesticMarketType, pageable: Pageable): Page<DomesticStock>
    
    /**
     * 종목명으로 검색 (부분 일치, 활성 종목만)
     */
    fun findByStockNameContainingAndIsActiveTrueOrderByStockNameAsc(stockName: String): List<DomesticStock>
    
    /**
     * 종목명으로 검색 페이징 (부분 일치, 활성 종목만)
     */
    fun findByStockNameContainingAndIsActiveTrue(stockName: String, pageable: Pageable): Page<DomesticStock>
    
    /**
     * 업종별 활성 종목 조회
     */
    fun findBySectorCodeAndIsActiveTrueOrderByStockCodeAsc(sectorCode: String): List<DomesticStock>
    
    /**
     * 여러 종목코드로 일괄 조회 (활성 종목만)
     */
    fun findByStockCodeInAndIsActiveTrueOrderByStockCodeAsc(stockCodes: List<String>): List<DomesticStock>
    
    /**
     * 종목코드 존재 여부 확인
     */
    fun existsByStockCode(stockCode: String): Boolean
    
    /**
     * 활성 종목코드 존재 여부 확인
     */
    fun existsByStockCodeAndIsActiveTrue(stockCode: String): Boolean
    
    /**
     * 시장별 종목 수 카운트 (활성 종목만)
     */
    fun countByMarketTypeAndIsActiveTrue(marketType: DomesticMarketType): Long
    
    /**
     * 전체 활성 종목 수 카운트
     */
    fun countByIsActiveTrue(): Long
    
    /**
     * 최근 업데이트된 종목들 조회
     */
    @Query("""
        SELECT d FROM DomesticStock d 
        WHERE d.isActive = true 
        AND d.updatedAt >= :since 
        ORDER BY d.updatedAt DESC
    """)
    fun findRecentlyUpdatedStocks(@Param("since") since: LocalDateTime): List<DomesticStock>
    
    /**
     * 시장별 종목 통계 조회
     */
    @Query("""
        SELECT d.marketType as marketType, 
               COUNT(*) as totalCount,
               COUNT(CASE WHEN d.isActive = true THEN 1 END) as activeCount
        FROM DomesticStock d 
        GROUP BY d.marketType
    """)
    fun findMarketStatistics(): List<MarketStatistics>
    
    /**
     * 업종별 종목 수 조회 (활성 종목만)
     */
    @Query("""
        SELECT d.sectorCode as sectorCode, COUNT(*) as count
        FROM DomesticStock d 
        WHERE d.isActive = true AND d.sectorCode IS NOT NULL
        GROUP BY d.sectorCode 
        ORDER BY count DESC
    """)
    fun findSectorStatistics(): List<SectorStatistics>
    
    /**
     * 종목명 또는 종목코드로 통합 검색 (활성 종목만)
     */
    @Query("""
        SELECT d FROM DomesticStock d 
        WHERE d.isActive = true 
        AND (UPPER(d.stockCode) LIKE UPPER(CONCAT('%', :keyword, '%')) 
             OR d.stockName LIKE CONCAT('%', :keyword, '%'))
        ORDER BY 
            CASE WHEN UPPER(d.stockCode) = UPPER(:keyword) THEN 1 ELSE 2 END,
            CASE WHEN d.stockName = :keyword THEN 1 ELSE 2 END,
            d.stockCode ASC
    """)
    fun searchByKeyword(@Param("keyword") keyword: String): List<DomesticStock>
    
    /**
     * 종목명 또는 종목코드로 통합 검색 페이징 (활성 종목만)
     */
    @Query("""
        SELECT d FROM DomesticStock d 
        WHERE d.isActive = true 
        AND (UPPER(d.stockCode) LIKE UPPER(CONCAT('%', :keyword, '%')) 
             OR d.stockName LIKE CONCAT('%', :keyword, '%'))
        ORDER BY 
            CASE WHEN UPPER(d.stockCode) = UPPER(:keyword) THEN 1 ELSE 2 END,
            CASE WHEN d.stockName = :keyword THEN 1 ELSE 2 END,
            d.stockCode ASC
    """)
    fun searchByKeyword(@Param("keyword") keyword: String, pageable: Pageable): Page<DomesticStock>
    
    /**
     * 인기 검색 종목 (상세정보가 많은 순)
     */
    @Query("""
        SELECT d FROM DomesticStock d 
        LEFT JOIN d.stockDetails sd 
        WHERE d.isActive = true 
        GROUP BY d.id 
        ORDER BY COUNT(sd.id) DESC
    """)
    fun findPopularStocks(pageable: Pageable): Page<DomesticStock>
}

/**
 * 시장 통계 DTO
 */
interface MarketStatistics {
    val marketType: DomesticMarketType
    val totalCount: Long
    val activeCount: Long
}

/**
 * 업종 통계 DTO
 */
interface SectorStatistics {
    val sectorCode: String
    val count: Long
}