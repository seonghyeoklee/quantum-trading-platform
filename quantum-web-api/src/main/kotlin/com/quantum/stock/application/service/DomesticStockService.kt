package com.quantum.stock.application.service

import com.quantum.stock.domain.DomesticStock
import com.quantum.stock.domain.DomesticStocksDetail
import com.quantum.stock.domain.StockDataType
import com.quantum.stock.infrastructure.persistence.DomesticStockRepository
import com.quantum.stock.infrastructure.persistence.DomesticStocksDetailRepository
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.time.LocalDate

/**
 * 국내주식 비즈니스 서비스
 * 
 * 데이터 무결성과 트랜잭션 경계를 보장하는 서비스 레이어
 * 가짜 데이터 생성을 방지하고 실제 데이터만 반환
 */
@Service
@Transactional(readOnly = true)
class DomesticStockService(
    private val domesticStockRepository: DomesticStockRepository,
    private val domesticStocksDetailRepository: DomesticStocksDetailRepository
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    /**
     * 종목 상세 정보 조회 (기간별)
     * 
     * 데이터 무결성 보장:
     * - 실제 데이터만 반환 (가짜 데이터 생성 금지)
     * - 데이터 검증 실패 시 빈 결과 반환
     * - 모든 DB 오류를 적절히 처리
     */
    fun getStockDetailsByPeriod(
        stockCode: String,
        startDate: LocalDate,
        endDate: LocalDate,
        dataType: StockDataType
    ): List<DomesticStocksDetail> {
        
        return try {
            logger.info("주식 상세정보 조회 시작 - stockCode: $stockCode, period: $startDate ~ $endDate, type: $dataType")
            
            // 1. 종목 존재 여부 검증 (실제 데이터만)
            val domesticStock = domesticStockRepository.findByStockCode(stockCode)
            if (domesticStock == null) {
                logger.warn("종목코드가 존재하지 않음: $stockCode")
                return emptyList() // 가짜 데이터 생성하지 않고 빈 리스트 반환
            }
            
            if (!domesticStock.isActive) {
                logger.warn("비활성화된 종목: $stockCode")
                return emptyList()
            }
            
            // 2. 실제 데이터 조회
            val stockDetails = domesticStocksDetailRepository.findByPeriod(
                stockCode = stockCode,
                dataType = dataType,
                startTime = startDate,
                endTime = endDate
            )
            
            // 3. 데이터 무결성 검증
            val validDetails = stockDetails.filter { detail ->
                validateStockDetail(detail)
            }
            
            if (validDetails.size < stockDetails.size) {
                logger.warn("일부 데이터가 유효성 검사에 실패: 전체 ${stockDetails.size}개 중 ${validDetails.size}개만 유효")
            }
            
            logger.info("주식 상세정보 조회 완료 - stockCode: $stockCode, 결과: ${validDetails.size}개")
            
            return validDetails
            
        } catch (exception: Exception) {
            logger.error("주식 상세정보 조회 실패 - stockCode: $stockCode", exception)
            // 절대로 가짜 데이터를 생성하지 않고 빈 리스트 반환
            emptyList()
        }
    }
    
    
    /**
     * 주식 상세 정보 데이터 검증
     * 
     * 가짜 데이터 방지를 위한 엄격한 검증
     */
    private fun validateStockDetail(detail: DomesticStocksDetail): Boolean {
        return try {
            // 1. 필수 필드 존재 확인
            if (detail.stockCode.isBlank() || detail.rawResponse == null) {
                return false
            }
            
            // 2. JSON 응답 데이터 유효성 확인
            val rawResponse = detail.rawResponse
            if (rawResponse.isEmpty()) {
                return false
            }
            
            // 3. 데이터 타입별 검증
            when (detail.dataType) {
                StockDataType.PRICE -> {
                    // 현재가 데이터 검증 - 가격이 0 이상이어야 함
                    val currentPrice = rawResponse["stck_prpr"]?.toString()?.toDoubleOrNull()
                    if (currentPrice == null || currentPrice <= 0) {
                        logger.debug("유효하지 않은 현재가: $currentPrice, stockCode: ${detail.stockCode}")
                        return false
                    }
                }
                StockDataType.CHART -> {
                    // 차트 데이터 검증 - OHLC 가격들이 유효해야 함
                    val openPrice = rawResponse["stck_oprc"]?.toString()?.toDoubleOrNull()
                    val highPrice = rawResponse["stck_hgpr"]?.toString()?.toDoubleOrNull()
                    val lowPrice = rawResponse["stck_lwpr"]?.toString()?.toDoubleOrNull()
                    val closePrice = rawResponse["stck_clpr"]?.toString()?.toDoubleOrNull()
                    
                    if (openPrice == null || highPrice == null || lowPrice == null || closePrice == null) {
                        return false
                    }
                    
                    if (openPrice <= 0 || highPrice <= 0 || lowPrice <= 0 || closePrice <= 0) {
                        return false
                    }
                    
                    // OHLC 관계 검증: Low ≤ Open/Close ≤ High
                    if (lowPrice > openPrice || lowPrice > closePrice || 
                        highPrice < openPrice || highPrice < closePrice) {
                        return false
                    }
                }
                else -> {
                    // 기타 데이터 타입도 기본적인 검증 수행
                }
            }
            
            true
            
        } catch (exception: Exception) {
            logger.debug("주식 상세정보 검증 실패: ${detail.stockCode}", exception)
            false
        }
    }
    
}

/**
 * 주식 데이터 서비스 예외 클래스
 */
class StockDataException(
    message: String,
    cause: Throwable? = null
) : RuntimeException(message, cause)