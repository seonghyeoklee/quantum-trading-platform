package com.quantum.stock.presentation.web

import com.quantum.stock.application.service.DomesticStockService
import com.quantum.stock.domain.DailyChartData
import com.quantum.stock.domain.DomesticStocksDetail
import com.quantum.stock.domain.StockDataType
import org.springframework.format.annotation.DateTimeFormat
import org.springframework.web.bind.annotation.*
import java.time.LocalDate

/**
 * 국내주식 상세정보 REST API 컨트롤러
 * 
 * 데이터 무결성 보장:
 * - 서비스 레이어를 통한 데이터 검증
 * - 가짜 데이터 생성 방지
 * - 실제 데이터만 응답
 */
@RestController
@RequestMapping("/api/v1/stocks/details")
class DomesticStockDetailController(
    private val domesticStockService: DomesticStockService
) {
    
    /**
     * 국내주식 상세정보 조회 (기간별)
     * 
     * @param stockCode 종목코드 (예: "005930")
     * @param startDate 조회 시작일 (YYYY-MM-DD)
     * @param endDate 조회 종료일 (YYYY-MM-DD)
     * @param dataType 데이터 타입 (PRICE, CHART, INDEX)
     * @return 검증된 실제 데이터만 반환 (가짜 데이터 절대 생성 안함)
     */
    @GetMapping
    fun getStockDetailsByPeriod(
        @RequestParam stockCode: String,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) startDate: LocalDate,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) endDate: LocalDate,
        @RequestParam(defaultValue = "CHART") dataType: StockDataType
    ): List<DomesticStocksDetail> {
        
        return domesticStockService.getStockDetailsByPeriod(
            stockCode = stockCode,
            startDate = startDate,
            endDate = endDate,
            dataType = dataType
        )
    }
    
    /**
     * 일별 차트 데이터 조회 (백테스팅 최적화)
     * 
     * @param stockCode 종목코드
     * @param startDate 조회 시작일
     * @param endDate 조회 종료일
     * @return 검증된 OHLCV 차트 데이터
     */
    @GetMapping("/chart")
    fun getDailyChartData(
        @RequestParam stockCode: String,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) startDate: LocalDate,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) endDate: LocalDate
    ): List<DailyChartData> {
        
        return domesticStockService.getDailyChartData(
            stockCode = stockCode,
            startDate = startDate,
            endDate = endDate
        )
    }
}