package com.quantum.stock.infrastructure.persistence

import com.quantum.stock.domain.DailyChartData
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.time.LocalDate

/**
 * 일별 차트 데이터 JPA Repository
 * 
 * 백테스팅과 차트 렌더링에 최적화된 Repository
 */
@Repository
interface DailyChartDataRepository : JpaRepository<DailyChartData, Long> {
    
    /**
     * 종목코드와 거래일 범위로 차트 데이터 조회
     * 
     * @param stockCode 종목코드
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 거래일 오름차순 정렬된 차트 데이터 리스트
     */
    fun findByStockCodeAndTradeDateBetween(
        stockCode: String,
        startDate: LocalDate,
        endDate: LocalDate
    ): List<DailyChartData>
    
    /**
     * 특정 종목의 최신 차트 데이터 조회
     * 
     * @param stockCode 종목코드
     * @return 가장 최근 차트 데이터 (없으면 null)
     */
    @Query("SELECT d FROM DailyChartData d WHERE d.stockCode = :stockCode ORDER BY d.tradeDate DESC LIMIT 1")
    fun findLatestByStockCode(@Param("stockCode") stockCode: String): DailyChartData?
    
    /**
     * 특정 종목의 차트 데이터 존재 여부 확인
     * 
     * @param stockCode 종목코드
     * @return 데이터 존재 여부
     */
    fun existsByStockCode(stockCode: String): Boolean
    
    /**
     * 특정 기간 동안의 거래량 상위 종목 조회
     * 
     * @param startDate 시작일
     * @param endDate 종료일
     * @param limit 조회 개수
     * @return 거래량 평균이 높은 순서로 정렬된 종목코드 리스트
     */
    @Query("""
        SELECT d.stockCode 
        FROM DailyChartData d 
        WHERE d.tradeDate BETWEEN :startDate AND :endDate
        GROUP BY d.stockCode 
        ORDER BY AVG(d.volume) DESC
        LIMIT :limit
    """)
    fun findTopVolumeStocks(
        @Param("startDate") startDate: LocalDate,
        @Param("endDate") endDate: LocalDate,
        @Param("limit") limit: Int
    ): List<String>
    
    /**
     * 종목별 데이터 개수 조회 (데이터 품질 확인용)
     * 
     * @param stockCode 종목코드
     * @return 해당 종목의 차트 데이터 개수
     */
    fun countByStockCode(stockCode: String): Long
}