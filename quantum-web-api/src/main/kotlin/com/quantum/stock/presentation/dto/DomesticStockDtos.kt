package com.quantum.stock.presentation.dto

import com.quantum.stock.domain.DomesticMarketType
import com.quantum.stock.domain.DomesticStock
import java.time.LocalDate
import java.time.LocalDateTime

/**
 * 국내주식 종목 리스트용 DTO
 * 
 * 종목 선택 UI에서 사용하는 경량 DTO
 */
data class DomesticStockListDto(
    val stockCode: String,
    val stockName: String,
    val marketType: DomesticMarketType,
    val isActive: Boolean,
    val sectorCode: String? = null,
    val listingDate: LocalDate? = null
) {
    companion object {
        fun from(stock: DomesticStock): DomesticStockListDto {
            return DomesticStockListDto(
                stockCode = stock.stockCode,
                stockName = stock.stockName,
                marketType = stock.marketType,
                isActive = stock.isActive,
                sectorCode = stock.sectorCode,
                listingDate = stock.listingDate
            )
        }
    }
}

/**
 * 국내주식 종목 리스트 응답 DTO (페이징 정보 포함)
 */
data class DomesticStockListResponse(
    val stocks: List<DomesticStockListDto>,
    val totalCount: Long,
    val currentPage: Int,
    val totalPages: Int,
    val pageSize: Int
) {
    companion object {
        fun from(
            stocks: List<DomesticStock>,
            totalCount: Long,
            currentPage: Int,
            pageSize: Int
        ): DomesticStockListResponse {
            val totalPages = if (totalCount > 0) ((totalCount - 1) / pageSize + 1).toInt() else 0
            
            return DomesticStockListResponse(
                stocks = stocks.map { DomesticStockListDto.from(it) },
                totalCount = totalCount,
                currentPage = currentPage,
                totalPages = totalPages,
                pageSize = pageSize
            )
        }
    }
}

/**
 * 국내주식 종목 검색 요청 DTO
 */
data class DomesticStockSearchRequest(
    val keyword: String,
    val marketType: DomesticMarketType? = null,
    val page: Int = 0,
    val size: Int = 20
) {
    init {
        require(keyword.isNotBlank()) { "검색어는 필수입니다" }
        require(page >= 0) { "페이지는 0 이상이어야 합니다" }
        require(size in 1..100) { "페이지 크기는 1~100 사이여야 합니다" }
    }
}

/**
 * 국내주식 종목 상세 정보 DTO
 */
data class DomesticStockDetailDto(
    val stockCode: String,
    val stockName: String,
    val marketType: DomesticMarketType,
    val isinCode: String? = null,
    val sectorCode: String? = null,
    val listingDate: LocalDate? = null,
    val isActive: Boolean,
    val createdAt: LocalDateTime,
    val updatedAt: LocalDateTime,
    val summary: String
) {
    companion object {
        fun from(stock: DomesticStock): DomesticStockDetailDto {
            return DomesticStockDetailDto(
                stockCode = stock.stockCode,
                stockName = stock.stockName,
                marketType = stock.marketType,
                isinCode = stock.isinCode,
                sectorCode = stock.sectorCode,
                listingDate = stock.listingDate,
                isActive = stock.isActive,
                createdAt = stock.createdAt,
                updatedAt = stock.updatedAt,
                summary = stock.getSummary()
            )
        }
    }
}