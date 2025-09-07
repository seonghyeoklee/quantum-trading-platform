package com.quantum.stock.infrastructure.persistence

import com.quantum.stock.domain.OverseasStockDetail
import com.quantum.stock.domain.OverseasExchange
import com.quantum.stock.domain.StockDataType
import com.quantum.stock.domain.DataQuality
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.time.LocalDate
import java.time.LocalDateTime

/**
 * 해외주식상세정보 Repository
 * 
 * DDD 기반 해외 주식 상세 데이터 접근 레이어
 */
@Repository
interface OverseasStockDetailRepository : JpaRepository<OverseasStockDetail, Long> {
    
    /**
     * 심볼과 거래소로 전체 상세정보 조회 (최신순)
     */
    fun findBySymbolAndExchangeOrderByRequestTimestampDesc(
        symbol: String, 
        exchange: OverseasExchange
    ): List<OverseasStockDetail>
    
    /**
     * 심볼과 거래소로 상세정보 페이징 조회 (최신순)
     */
    fun findBySymbolAndExchange(
        symbol: String, 
        exchange: OverseasExchange, 
        pageable: Pageable
    ): Page<OverseasStockDetail>
    
    /**
     * 심볼, 거래소, 데이터 타입으로 조회 (최신순)
     */
    fun findBySymbolAndExchangeAndDataTypeOrderByRequestTimestampDesc(
        symbol: String, 
        exchange: OverseasExchange, 
        dataType: StockDataType
    ): List<OverseasStockDetail>
    
    /**
     * 심볼, 거래소, 데이터 타입으로 최신 1건 조회
     */
    fun findFirstBySymbolAndExchangeAndDataTypeOrderByRequestTimestampDesc(
        symbol: String, 
        exchange: OverseasExchange, 
        dataType: StockDataType
    ): OverseasStockDetail?
    
    /**
     * 심볼별 최신 현재가 정보 조회 (성공 응답만)
     */
    fun findFirstBySymbolAndExchangeAndDataTypeAndResponseCodeOrderByRequestTimestampDesc(
        symbol: String,
        exchange: OverseasExchange,
        dataType: StockDataType,
        responseCode: String
    ): OverseasStockDetail?
    
    /**
     * 심볼별 양질의 최신 데이터 조회
     */
    @Query("""
        SELECT d FROM OverseasStockDetail d 
        WHERE d.symbol = :symbol 
        AND d.exchange = :exchange
        AND d.dataType = :dataType
        AND d.responseCode = '0'
        AND d.dataQuality IN ('EXCELLENT', 'GOOD')
        ORDER BY d.requestTimestamp DESC
    """)
    fun findLatestGoodQualityData(
        @Param("symbol") symbol: String,
        @Param("exchange") exchange: OverseasExchange,
        @Param("dataType") dataType: StockDataType
    ): List<OverseasStockDetail>
    
    /**
     * 특정 날짜의 차트 데이터 조회
     */
    fun findBySymbolAndExchangeAndDataTypeAndTradeDateOrderByRequestTimestampDesc(
        symbol: String,
        exchange: OverseasExchange,
        dataType: StockDataType,
        tradeDate: LocalDate
    ): List<OverseasStockDetail>
    
    /**
     * 특정 기간의 상세정보 조회
     */
    @Query("""
        SELECT d FROM OverseasStockDetail d 
        WHERE d.symbol = :symbol 
        AND d.exchange = :exchange
        AND d.dataType = :dataType
        AND d.requestTimestamp BETWEEN :startTime AND :endTime
        ORDER BY d.requestTimestamp DESC
    """)
    fun findByPeriod(
        @Param("symbol") symbol: String,
        @Param("exchange") exchange: OverseasExchange,
        @Param("dataType") dataType: StockDataType,
        @Param("startTime") startTime: LocalDateTime,
        @Param("endTime") endTime: LocalDateTime
    ): List<OverseasStockDetail>
    
    /**
     * 여러 심볼의 최신 현재가 조회 (성공 응답, 양질 데이터만)
     */
    @Query("""
        SELECT d FROM OverseasStockDetail d 
        WHERE d.symbol IN :symbols 
        AND d.exchange = :exchange
        AND d.dataType = 'PRICE'
        AND d.responseCode = '0'
        AND d.dataQuality IN ('EXCELLENT', 'GOOD')
        AND d.id IN (
            SELECT MAX(d2.id) FROM OverseasStockDetail d2 
            WHERE d2.symbol = d.symbol 
            AND d2.exchange = d.exchange
            AND d2.dataType = 'PRICE'
            AND d2.responseCode = '0'
            AND d2.dataQuality IN ('EXCELLENT', 'GOOD')
        )
        ORDER BY d.symbol ASC
    """)
    fun findLatestPricesForStocks(
        @Param("symbols") symbols: List<String>,
        @Param("exchange") exchange: OverseasExchange
    ): List<OverseasStockDetail>
    
    /**
     * 오늘 수집된 데이터 개수 조회
     */
    @Query("""
        SELECT d.data_type as dataType, d.exchange as exchange, COUNT(*) as count, COUNT(DISTINCT d.symbol) as uniqueStocks
        FROM overseas_stock_detail d 
        WHERE DATE(d.created_at) = CURRENT_DATE
        GROUP BY d.data_type, d.exchange
        ORDER BY d.exchange, d.data_type
    """, nativeQuery = true)
    fun findTodayDataStatistics(): List<OverseasDailyDataStatistics>
    
    /**
     * 특정 날짜 수집 데이터 통계
     */
    @Query("""
        SELECT d.data_type as dataType, d.exchange as exchange, COUNT(*) as count, COUNT(DISTINCT d.symbol) as uniqueStocks
        FROM overseas_stock_detail d 
        WHERE DATE(d.created_at) = :date
        GROUP BY d.data_type, d.exchange
        ORDER BY d.exchange, d.data_type
    """, nativeQuery = true)
    fun findDataStatisticsByDate(@Param("date") date: LocalDate): List<OverseasDailyDataStatistics>
    
    /**
     * 데이터 품질별 통계 조회
     */
    @Query("""
        SELECT d.data_quality as quality, COUNT(*) as count
        FROM overseas_stock_detail d 
        WHERE DATE(d.created_at) = CURRENT_DATE
        GROUP BY d.data_quality
        ORDER BY count DESC
    """, nativeQuery = true)
    fun findTodayQualityStatistics(): List<OverseasQualityStatistics>
    
    /**
     * API 엔드포인트별 호출 통계 (오늘)
     */
    @Query("""
        SELECT d.api_endpoint as endpoint, COUNT(*) as count, 
               COUNT(CASE WHEN d.response_code = '0' THEN 1 END) as successCount
        FROM overseas_stock_detail d 
        WHERE DATE(d.request_timestamp) = CURRENT_DATE
        GROUP BY d.api_endpoint
        ORDER BY count DESC
    """, nativeQuery = true)
    fun findTodayEndpointStatistics(): List<OverseasEndpointStatistics>
    
    /**
     * 최근 N일간의 데이터 보유 종목 수
     */
    @Query("""
        SELECT COUNT(DISTINCT CONCAT(d.symbol, ':', d.exchange)) 
        FROM overseas_stock_detail d 
        WHERE d.request_timestamp >= :since
        AND d.response_code = '0'
        AND d.data_quality IN ('EXCELLENT', 'GOOD')
    """, nativeQuery = true)
    fun countActiveStocksSince(@Param("since") since: LocalDateTime): Long
    
    /**
     * 특정 종목의 데이터 수집 이력 조회 (요약)
     */
    @Query("""
        SELECT DATE(d.request_timestamp) as date, d.data_type as dataType, COUNT(*) as count
        FROM overseas_stock_detail d 
        WHERE d.symbol = :symbol 
        AND d.exchange = :exchange
        AND d.request_timestamp >= :since
        GROUP BY DATE(d.request_timestamp), d.data_type
        ORDER BY date DESC, dataType
    """, nativeQuery = true)
    fun findDataHistoryForStock(
        @Param("symbol") symbol: String,
        @Param("exchange") exchange: OverseasExchange,
        @Param("since") since: LocalDateTime
    ): List<OverseasDataHistoryStatistics>
    
    /**
     * 오류 데이터 조회 (오늘)
     */
    @Query("""
        SELECT d FROM OverseasStockDetail d 
        WHERE CAST(d.requestTimestamp AS date) = CURRENT_DATE
        AND (d.responseCode != '0' OR d.responseCode IS NULL)
        ORDER BY d.requestTimestamp DESC
    """)
    fun findTodayErrorData(pageable: Pageable): Page<OverseasStockDetail>
    
    /**
     * 특정 종목의 시계열 차트 데이터 조회 (기간 지정)
     */
    @Query("""
        SELECT d FROM OverseasStockDetail d 
        WHERE d.symbol = :symbol 
        AND d.exchange = :exchange
        AND d.dataType = 'CHART'
        AND d.responseCode = '0'
        AND d.dataQuality IN ('EXCELLENT', 'GOOD')
        AND (:startDate IS NULL OR d.tradeDate >= :startDate)
        AND (:endDate IS NULL OR d.tradeDate <= :endDate)
        ORDER BY d.tradeDate ASC, d.requestTimestamp DESC
    """)
    fun findChartDataByPeriod(
        @Param("symbol") symbol: String,
        @Param("exchange") exchange: OverseasExchange,
        @Param("startDate") startDate: LocalDate?,
        @Param("endDate") endDate: LocalDate?,
        pageable: Pageable
    ): Page<OverseasStockDetail>
    
    /**
     * 거래소별 통계 조회
     */
    @Query("""
        SELECT d.exchange as exchange, COUNT(*) as totalCount,
               COUNT(CASE WHEN d.responseCode = '0' THEN 1 END) as successCount,
               COUNT(DISTINCT d.symbol) as uniqueSymbols
        FROM OverseasStockDetail d 
        WHERE CAST(d.requestTimestamp AS date) = CURRENT_DATE
        GROUP BY d.exchange
        ORDER BY totalCount DESC
    """)
    fun findTodayExchangeStatistics(): List<OverseasExchangeStatistics>
    
    /**
     * 데이터 정리 - 30일 이전 중복 데이터 중 최신 것만 남기고 삭제할 대상 조회
     */
    @Query("""
        SELECT d.id FROM OverseasStockDetail d 
        WHERE d.requestTimestamp < :cutoffDate
        AND d.id NOT IN (
            SELECT MAX(d2.id) FROM OverseasStockDetail d2 
            WHERE d2.symbol = d.symbol 
            AND d2.exchange = d.exchange
            AND d2.dataType = d.dataType 
            AND CAST(d2.tradeDate AS date) = CAST(d.tradeDate AS date)
            AND d2.requestTimestamp < :cutoffDate
        )
    """)
    fun findDuplicateDataForCleanup(@Param("cutoffDate") cutoffDate: LocalDateTime): List<Long>
}

/**
 * 해외 일별 데이터 통계 DTO
 */
interface OverseasDailyDataStatistics {
    val dataType: StockDataType
    val exchange: OverseasExchange
    val count: Long
    val uniqueStocks: Long
}

/**
 * 해외 데이터 품질 통계 DTO
 */
interface OverseasQualityStatistics {
    val quality: DataQuality
    val count: Long
}

/**
 * 해외 API 엔드포인트 통계 DTO
 */
interface OverseasEndpointStatistics {
    val endpoint: String
    val count: Long
    val successCount: Long
}

/**
 * 해외 데이터 수집 이력 통계 DTO
 */
interface OverseasDataHistoryStatistics {
    val date: LocalDate
    val dataType: StockDataType
    val count: Long
}

/**
 * 해외 거래소 통계 DTO
 */
interface OverseasExchangeStatistics {
    val exchange: OverseasExchange
    val totalCount: Long
    val successCount: Long
    val uniqueSymbols: Long
}