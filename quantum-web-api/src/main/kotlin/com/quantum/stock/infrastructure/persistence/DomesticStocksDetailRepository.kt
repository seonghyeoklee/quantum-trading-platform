package com.quantum.stock.infrastructure.persistence

import com.quantum.stock.domain.DomesticStocksDetail
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
 * 국내주식상세정보 Repository
 * 
 * DDD 기반 국내 주식 상세 데이터 접근 레이어
 */
@Repository
interface DomesticStocksDetailRepository : JpaRepository<DomesticStocksDetail, Long> {
    
    /**
     * 종목코드로 전체 상세정보 조회 (최신순)
     */
    fun findByStockCodeOrderByRequestTimestampDesc(stockCode: String): List<DomesticStocksDetail>
    
    /**
     * 종목코드로 상세정보 페이징 조회 (최신순)
     */
    fun findByStockCode(stockCode: String, pageable: Pageable): Page<DomesticStocksDetail>
    
    /**
     * 종목코드와 데이터 타입으로 조회 (최신순)
     */
    fun findByStockCodeAndDataTypeOrderByRequestTimestampDesc(
        stockCode: String, 
        dataType: StockDataType
    ): List<DomesticStocksDetail>
    
    /**
     * 종목코드와 데이터 타입으로 최신 1건 조회
     */
    fun findFirstByStockCodeAndDataTypeOrderByRequestTimestampDesc(
        stockCode: String, 
        dataType: StockDataType
    ): DomesticStocksDetail?
    
    /**
     * 종목코드별 최신 현재가 정보 조회 (성공 응답만)
     */
    fun findFirstByStockCodeAndDataTypeAndResponseCodeOrderByRequestTimestampDesc(
        stockCode: String,
        dataType: StockDataType,
        responseCode: String
    ): DomesticStocksDetail?
    
    /**
     * 종목코드별 양질의 최신 데이터 조회
     */
    @Query(
        """
        SELECT d FROM DomesticStocksDetail d 
        WHERE d.stockCode = :stockCode 
        AND d.dataType = :dataType
        AND d.responseCode = '0'
        AND d.dataQuality IN ('EXCELLENT', 'GOOD')
        ORDER BY d.requestTimestamp DESC
    """
    )
    fun findLatestGoodQualityData(
        @Param("stockCode") stockCode: String,
        @Param("dataType") dataType: StockDataType
    ): List<DomesticStocksDetail>
    
    /**
     * 특정 날짜의 차트 데이터 조회
     */
    fun findByStockCodeAndDataTypeAndTradeDateOrderByRequestTimestampDesc(
        stockCode: String,
        dataType: StockDataType,
        tradeDate: LocalDate
    ): List<DomesticStocksDetail>
    
    /**
     * 특정 기간의 상세정보 조회
     */
    @Query(
        """
        SELECT d FROM DomesticStocksDetail d 
        WHERE d.stockCode = :stockCode 
        AND d.dataType = :dataType
        AND d.tradeDate BETWEEN :startTime AND :endTime
        ORDER BY d.requestTimestamp DESC
    """
    )
    fun findByPeriod(
        @Param("stockCode") stockCode: String,
        @Param("dataType") dataType: StockDataType,
        @Param("startTime") startTime: LocalDate,
        @Param("endTime") endTime: LocalDate
    ): List<DomesticStocksDetail>
    
    /**
     * 여러 종목의 최신 현재가 조회 (성공 응답, 양질 데이터만)
     */
    @Query(
        """
        SELECT d FROM DomesticStocksDetail d 
        WHERE d.stockCode IN :stockCodes 
        AND d.dataType = 'PRICE'
        AND d.responseCode = '0'
        AND d.dataQuality IN ('EXCELLENT', 'GOOD')
        AND d.id IN (
            SELECT MAX(d2.id) FROM DomesticStocksDetail d2 
            WHERE d2.stockCode = d.stockCode 
            AND d2.dataType = 'PRICE'
            AND d2.responseCode = '0'
            AND d2.dataQuality IN ('EXCELLENT', 'GOOD')
        )
        ORDER BY d.stockCode ASC
    """
    )
    fun findLatestPricesForStocks(@Param("stockCodes") stockCodes: List<String>): List<DomesticStocksDetail>
    
    /**
     * 오늘 수집된 데이터 개수 조회
     */
    @Query("""
        SELECT d.data_type as dataType, COUNT(*) as count, COUNT(DISTINCT d.stock_code) as uniqueStocks
        FROM domestic_stocks_detail d 
        WHERE DATE(d.created_at) = CURRENT_DATE
        GROUP BY d.data_type
        ORDER BY d.data_type
    """, nativeQuery = true)
    fun findTodayDataStatistics(): List<DailyDataStatistics>
    
    /**
     * 특정 날짜 수집 데이터 통계
     */
    @Query("""
        SELECT d.data_type as dataType, COUNT(*) as count, COUNT(DISTINCT d.stock_code) as uniqueStocks
        FROM domestic_stocks_detail d 
        WHERE DATE(d.created_at) = :date
        GROUP BY d.data_type
        ORDER BY d.data_type
    """, nativeQuery = true)
    fun findDataStatisticsByDate(@Param("date") date: LocalDate): List<DailyDataStatistics>
    
    /**
     * 데이터 품질별 통계 조회
     */
    @Query("""
        SELECT d.data_quality as quality, COUNT(*) as count
        FROM domestic_stocks_detail d 
        WHERE DATE(d.created_at) = CURRENT_DATE
        GROUP BY d.data_quality
        ORDER BY count DESC
    """, nativeQuery = true)
    fun findTodayQualityStatistics(): List<QualityStatistics>
    
    /**
     * API 엔드포인트별 호출 통계 (오늘)
     */
    @Query("""
        SELECT d.api_endpoint as endpoint, COUNT(*) as count, 
               COUNT(CASE WHEN d.response_code = '0' THEN 1 END) as successCount
        FROM domestic_stocks_detail d 
        WHERE DATE(d.request_timestamp) = CURRENT_DATE
        GROUP BY d.api_endpoint
        ORDER BY count DESC
    """, nativeQuery = true)
    fun findTodayEndpointStatistics(): List<EndpointStatistics>
    
    /**
     * 최근 N일간의 데이터 보유 종목 수
     */
    @Query("""
        SELECT COUNT(DISTINCT d.stock_code) 
        FROM domestic_stocks_detail d 
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
        FROM domestic_stocks_detail d 
        WHERE d.stock_code = :stockCode 
        AND d.request_timestamp >= :since
        GROUP BY DATE(d.request_timestamp), d.data_type
        ORDER BY date DESC, dataType
    """, nativeQuery = true)
    fun findDataHistoryForStock(
        @Param("stockCode") stockCode: String,
        @Param("since") since: LocalDateTime
    ): List<DataHistoryStatistics>
    
    /**
     * 오류 데이터 조회 (오늘)
     */
    @Query(
        """
        SELECT d FROM DomesticStocksDetail d 
        WHERE CAST(d.requestTimestamp AS date) = CURRENT_DATE
        AND (d.responseCode != '0' OR d.responseCode IS NULL)
        ORDER BY d.requestTimestamp DESC
    """
    )
    fun findTodayErrorData(pageable: Pageable): Page<DomesticStocksDetail>
    
    /**
     * 특정 종목의 시계열 차트 데이터 조회 (기간 지정)
     */
    @Query(
        """
        SELECT d FROM DomesticStocksDetail d 
        WHERE d.stockCode = :stockCode 
        AND d.dataType = 'CHART'
        AND d.responseCode = '0'
        AND d.dataQuality IN ('EXCELLENT', 'GOOD')
        AND (:startDate IS NULL OR d.tradeDate >= :startDate)
        AND (:endDate IS NULL OR d.tradeDate <= :endDate)
        ORDER BY d.tradeDate ASC, d.requestTimestamp DESC
    """
    )
    fun findChartDataByPeriod(
        @Param("stockCode") stockCode: String,
        @Param("startDate") startDate: LocalDate?,
        @Param("endDate") endDate: LocalDate?,
        pageable: Pageable
    ): Page<DomesticStocksDetail>
    
    /**
     * 데이터 정리 - 30일 이전 중복 데이터 중 최신 것만 남기고 삭제할 대상 조회
     */
    @Query(
        """
        SELECT d.id FROM DomesticStocksDetail d 
        WHERE d.requestTimestamp < :cutoffDate
        AND d.id NOT IN (
            SELECT MAX(d2.id) FROM DomesticStocksDetail d2 
            WHERE d2.stockCode = d.stockCode 
            AND d2.dataType = d.dataType 
            AND CAST(d2.tradeDate AS date) = CAST(d.tradeDate AS date)
            AND d2.requestTimestamp < :cutoffDate
        )
    """
    )
    fun findDuplicateDataForCleanup(@Param("cutoffDate") cutoffDate: LocalDateTime): List<Long>
}

/**
 * 일별 데이터 통계 DTO
 */
interface DailyDataStatistics {
    val dataType: StockDataType
    val count: Long
    val uniqueStocks: Long
}

/**
 * 데이터 품질 통계 DTO
 */
interface QualityStatistics {
    val quality: DataQuality
    val count: Long
}

/**
 * API 엔드포인트 통계 DTO
 */
interface EndpointStatistics {
    val endpoint: String
    val count: Long
    val successCount: Long
}

/**
 * 데이터 수집 이력 통계 DTO
 */
interface DataHistoryStatistics {
    val date: LocalDate
    val dataType: StockDataType
    val count: Long
}