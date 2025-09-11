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

/**
 * KIS API 상세 정보가 포함된 종목 정보 DTO
 * 
 * 기본 종목 정보 + KIS API에서 가져온 실시간 데이터
 */
data class DomesticStockWithKisDetailDto(
    // 기본 종목 정보
    val stockCode: String,
    val stockName: String,
    val marketType: DomesticMarketType,
    val sectorCode: String? = null,
    val listingDate: LocalDate? = null,
    
    // KIS API 실시간 데이터
    val kisDetail: KisStockDetailInfo? = null,
    val dataUpdatedAt: LocalDateTime? = null
) {
    companion object {
        fun from(stock: DomesticStock, kisDetail: KisStockDetailInfo? = null): DomesticStockWithKisDetailDto {
            return DomesticStockWithKisDetailDto(
                stockCode = stock.stockCode,
                stockName = stock.stockName,
                marketType = stock.marketType,
                sectorCode = stock.sectorCode,
                listingDate = stock.listingDate,
                kisDetail = kisDetail,
                dataUpdatedAt = if (kisDetail != null) LocalDateTime.now() else null
            )
        }
    }
}

/**
 * KIS API 상세 정보
 * 
 * KIS Adapter에서 받은 데이터를 클라이언트 친화적으로 변환
 */
data class KisStockDetailInfo(
    // 현재가 정보
    val currentPrice: Long,              // 현재가
    val previousDayChange: Long,         // 전일대비
    val changeRate: Double,              // 등락률 (%)
    val changeSign: PriceChangeSign,     // 등락 구분
    val volume: Long,                    // 거래량
    val tradeAmount: Long,              // 거래대금
    
    // 가격 정보
    val openPrice: Long,                // 시가
    val highPrice: Long,                // 고가
    val lowPrice: Long,                 // 저가
    val upperLimit: Long,               // 상한가
    val lowerLimit: Long,               // 하한가
    
    // 재무비율
    val per: Double,                    // PER
    val pbr: Double,                    // PBR
    val eps: Long,                      // EPS
    val bps: Long,                      // BPS
    val marketCap: Long,                // 시가총액 (억원)
    
    // 기술적 지표
    val week52High: Long,               // 52주 최고가
    val week52Low: Long,                // 52주 최저가
    val week52HighDate: String,         // 52주 최고가 달성일
    val week52LowDate: String,          // 52주 최저가 달성일
    val day250High: Long,               // 250일 최고가
    val day250Low: Long,                // 250일 최저가
    val yearHigh: Long,                 // 연중 최고가
    val yearLow: Long,                  // 연중 최저가
    
    // 시장 정보
    val foreignOwnership: Double,       // 외국인 지분율 (%)
    val volumeTurnover: Double,         // 거래량 회전율
    val marketName: String,             // 시장명
    val sectorName: String,             // 업종명
    
    // 기타 정보
    val listedShares: Long,             // 상장주수
    val settlementMonth: String,        // 결산월
    val capital: String,                // 자본금
    val faceValue: Long                 // 액면가
)

/**
 * 가격 변동 구분
 */
enum class PriceChangeSign(val code: String, val description: String, val displayName: String) {
    RISE("2", "상승", "▲"),
    FLAT("3", "보합", "-"),
    FALL("5", "하락", "▼"),
    UNKNOWN("", "알 수 없음", "?");
    
    companion object {
        fun fromCode(code: String): PriceChangeSign {
            return values().find { it.code == code } ?: UNKNOWN
        }
    }
}