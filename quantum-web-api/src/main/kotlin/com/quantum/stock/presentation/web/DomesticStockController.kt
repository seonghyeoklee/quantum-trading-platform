package com.quantum.stock.presentation.web

import com.quantum.stock.domain.DomesticMarketType
import com.quantum.stock.infrastructure.persistence.DomesticStockRepository
import com.quantum.stock.application.service.DomesticStockService
import com.quantum.stock.presentation.dto.DomesticStockDetailDto
import com.quantum.stock.presentation.dto.DomesticStockListResponse
import com.quantum.stock.presentation.dto.DomesticStockSearchRequest
import com.quantum.stock.presentation.dto.DomesticStockWithKisDetailDto
// import io.github.logtree.spring.annotation.Traceable // 자동 추적으로 더 이상 불필요
import org.slf4j.LoggerFactory
import org.springframework.data.domain.PageRequest
import org.springframework.data.domain.Sort
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import kotlinx.coroutines.runBlocking

/**
 * 국내주식 종목 API 컨트롤러
 * 
 * 종목 리스트 조회, 검색, 상세 조회 기능 제공
 */
@RestController
@RequestMapping("/api/v1/stocks/domestic")
@CrossOrigin(origins = ["http://quantum-trading.com:3000", "http://localhost:3000"])
class DomesticStockController(
    private val domesticStockRepository: DomesticStockRepository,
    private val domesticStockService: DomesticStockService
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    /**
     * 국내주식 종목 전체 리스트 조회 (페이징)
     */
    @GetMapping
    // @Traceable - 자동 추적으로 더 이상 불필요
    fun getDomesticStocks(
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "20") size: Int,
        @RequestParam(required = false) marketType: DomesticMarketType?
    ): ResponseEntity<DomesticStockListResponse> {
        
        return try {
            logger.info("국내주식 종목 리스트 조회 - page: $page, size: $size, marketType: $marketType")
            
            // 페이지 크기 제한 (최대 100개)
            val validSize = minOf(size, 100)
            val pageable = PageRequest.of(page, validSize, Sort.by("stockCode").ascending())
            
            val stockPage = if (marketType != null) {
                domesticStockRepository.findByMarketTypeAndIsActiveTrue(marketType, pageable)
            } else {
                domesticStockRepository.findByIsActiveTrue(pageable)
            }
            
            val response = DomesticStockListResponse.from(
                stocks = stockPage.content,
                totalCount = stockPage.totalElements,
                currentPage = page,
                pageSize = validSize
            )
            
            logger.info("국내주식 종목 리스트 조회 완료 - 조회된 종목 수: ${response.stocks.size}, 전체: ${response.totalCount}")
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("국내주식 종목 리스트 조회 실패", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * 국내주식 종목 검색 (종목명, 종목코드)
     */
    @GetMapping("/search")
    // @Traceable - 자동 추적으로 더 이상 불필요
    fun searchDomesticStocks(
        @RequestParam keyword: String,
        @RequestParam(required = false) marketType: DomesticMarketType?,
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "20") size: Int
    ): ResponseEntity<DomesticStockListResponse> {
        
        return try {
            logger.info("국내주식 종목 검색 - keyword: '$keyword', marketType: $marketType")
            
            // 검색어 유효성 검증
            if (keyword.isBlank()) {
                logger.warn("검색어가 비어있음")
                return ResponseEntity.badRequest().build()
            }
            
            val validSize = minOf(size, 100)
            val pageable = PageRequest.of(page, validSize)
            
            // 키워드로 검색 (종목명 또는 종목코드)
            val searchResults = domesticStockRepository.searchByKeyword(keyword.trim(), pageable)
            
            // 마켓 타입 필터링 (필요한 경우)
            val filteredResults = if (marketType != null) {
                searchResults.content.filter { it.marketType == marketType }
            } else {
                searchResults.content
            }
            
            val response = DomesticStockListResponse.from(
                stocks = filteredResults,
                totalCount = filteredResults.size.toLong(),
                currentPage = page,
                pageSize = validSize
            )
            
            logger.info("국내주식 종목 검색 완료 - 검색 결과: ${response.stocks.size}건")
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("국내주식 종목 검색 실패 - keyword: '$keyword'", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * 특정 종목 상세 정보 조회
     */
    @GetMapping("/{stockCode}")
    // @Traceable - 자동 추적으로 더 이상 불필요
    fun getDomesticStock(@PathVariable stockCode: String): ResponseEntity<DomesticStockDetailDto> {
        
        return try {
            logger.info("국내주식 종목 상세 조회 - stockCode: $stockCode")
            
            // 종목코드 유효성 검증
            if (!stockCode.matches(Regex("^[A-Z0-9]{6}$"))) {
                logger.warn("유효하지 않은 종목코드 형식: $stockCode")
                return ResponseEntity.badRequest().build()
            }
            
            val stock = domesticStockRepository.findByStockCodeAndIsActiveTrue(stockCode)
            
            if (stock == null) {
                logger.warn("종목을 찾을 수 없음: $stockCode")
                return ResponseEntity.notFound().build()
            }
            
            val response = DomesticStockDetailDto.from(stock)
            
            logger.info("국내주식 종목 상세 조회 완료 - ${stock.stockName} (${stock.stockCode})")
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("국내주식 종목 상세 조회 실패 - stockCode: $stockCode", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * KIS API 상세 정보가 포함된 종목 정보 조회
     */
    @GetMapping("/{stockCode}/detail")
    // @Traceable - 자동 추적으로 더 이상 불필요
    fun getDomesticStockWithKisDetail(@PathVariable stockCode: String): ResponseEntity<DomesticStockWithKisDetailDto> {
        
        return try {
            logger.info("국내주식 KIS 상세 정보 조회 - stockCode: $stockCode")
            
            // 종목코드 유효성 검증
            if (!stockCode.matches(Regex("^[A-Z0-9]{6}$"))) {
                logger.warn("유효하지 않은 종목코드 형식: $stockCode")
                return ResponseEntity.badRequest().build()
            }
            
            // 기본 종목 정보 조회
            val stock = domesticStockRepository.findByStockCodeAndIsActiveTrue(stockCode)
            if (stock == null) {
                logger.warn("종목을 찾을 수 없음: $stockCode")
                return ResponseEntity.notFound().build()
            }
            
            // KIS API 상세 정보 조회 (비동기 처리)
            val kisDetail = runBlocking {
                domesticStockService.getKisStockDetail(stockCode)
            }
            
            val response = DomesticStockWithKisDetailDto.from(stock, kisDetail)
            
            if (kisDetail != null) {
                logger.info("국내주식 KIS 상세 정보 조회 완료 - ${stock.stockName} (${stock.stockCode}), 현재가: ${kisDetail.currentPrice}")
            } else {
                logger.warn("KIS API 상세 정보 조회 실패 - ${stock.stockName} (${stock.stockCode})")
            }
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("국내주식 KIS 상세 정보 조회 실패 - stockCode: $stockCode", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
}