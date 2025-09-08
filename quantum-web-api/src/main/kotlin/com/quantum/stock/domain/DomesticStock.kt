package com.quantum.stock.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import org.hibernate.annotations.Comment
import java.time.LocalDate

/**
 * 국내주식종목 엔티티
 * 
 * KOSPI/KOSDAQ 상장 종목의 기본 정보를 관리하는 DDD 기반 엔티티
 */
@Entity
@Table(
    name = "domestic_stocks",
    indexes = [
        Index(name = "idx_domestic_stocks_code", columnList = "stock_code"),
        Index(name = "idx_domestic_stocks_market", columnList = "market_type"),
        Index(name = "idx_domestic_stocks_name", columnList = "stock_name"),
        Index(name = "idx_domestic_stocks_active", columnList = "is_active")
    ],
    uniqueConstraints = [
        UniqueConstraint(name = "uk_domestic_stock_code", columnNames = ["stock_code"])
    ]
)
@Comment("국내주식종목 - KOSPI/KOSDAQ 상장 종목 정보 (DDD 설계)")
class DomesticStock(
    /**
     * 종목코드 (6자리)
     */
    @Column(name = "stock_code", nullable = false, length = 6)
    @Comment("종목코드 (6자리)")
    var stockCode: String = "",
    
    /**
     * 종목명
     */
    @Column(name = "stock_name", nullable = false, length = 100)
    @Comment("종목명")
    var stockName: String = "",
    
    /**
     * 시장구분
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "market_type", nullable = false, length = 10)
    @Comment("시장구분 (KOSPI/KOSDAQ)")
    var marketType: DomesticMarketType = DomesticMarketType.KOSPI,
    
    /**
     * ISIN 코드 (12자리)
     */
    @Column(name = "isin_code", length = 12)
    @Comment("ISIN 코드 (12자리)")
    var isinCode: String? = null,
    
    /**
     * 업종코드
     */
    @Column(name = "sector_code", length = 6)
    @Comment("업종코드")
    var sectorCode: String? = null,
    
    /**
     * 상장일
     */
    @Column(name = "listing_date")
    @Comment("상장일")
    var listingDate: LocalDate? = null,
    
    /**
     * 원본 고정길이 데이터
     */
    @Column(name = "raw_data", columnDefinition = "TEXT")
    @Comment("원본 고정길이 데이터")
    var rawData: String? = null,
    
    /**
     * 활성 상태
     */
    @Column(name = "is_active", nullable = false)
    @Comment("활성 상태")
    var isActive: Boolean = true

) : BaseEntity() {
    
    /**
     * JPA를 위한 기본 생성자
     */
    protected constructor() : this(
        stockCode = "",
        stockName = "",
        marketType = DomesticMarketType.KOSPI
    )
    
    /**
     * 종목 상세정보와의 연관관계
     */
    @OneToMany(
        mappedBy = "domesticStock",
        cascade = [CascadeType.ALL],
        fetch = FetchType.LAZY
    )
    @com.fasterxml.jackson.annotation.JsonIgnore
    var stockDetails: MutableList<DomesticStocksDetail> = mutableListOf()
    
    /**
     * KOSPI 종목인지 확인
     */
    fun isKospi(): Boolean {
        return marketType == DomesticMarketType.KOSPI
    }
    
    /**
     * KOSDAQ 종목인지 확인
     */
    fun isKosdaq(): Boolean {
        return marketType == DomesticMarketType.KOSDAQ
    }
    
    /**
     * 활성 종목인지 확인
     */
    fun isActiveStock(): Boolean {
        return isActive
    }
    
    /**
     * 종목 비활성화
     */
    fun deactivate() {
        this.isActive = false
    }
    
    /**
     * 종목 활성화
     */
    fun activate() {
        this.isActive = true
    }
    
    /**
     * 종목 정보 업데이트
     */
    fun updateStockInfo(
        stockName: String? = null,
        marketType: DomesticMarketType? = null,
        sectorCode: String? = null,
        listingDate: LocalDate? = null
    ) {
        stockName?.let { this.stockName = it }
        marketType?.let { this.marketType = it }
        sectorCode?.let { this.sectorCode = it }
        listingDate?.let { this.listingDate = it }
    }
    
    /**
     * 종목 요약 정보 생성
     */
    fun getSummary(): String {
        val status = if (isActive) "활성" else "비활성"
        return "$stockCode ($stockName) [$marketType] - $status"
    }
    
    /**
     * 최신 주식 상세정보 조회
     */
    @com.fasterxml.jackson.annotation.JsonIgnore
    fun getLatestDetail(): DomesticStocksDetail? {
        return stockDetails
            .filter { it.dataQuality in listOf(DataQuality.EXCELLENT, DataQuality.GOOD) }
            .maxByOrNull { it.requestTimestamp }
    }
    
    /**
     * 특정 타입의 최신 상세정보 조회
     */
    @com.fasterxml.jackson.annotation.JsonIgnore
    fun getLatestDetailByType(dataType: StockDataType): DomesticStocksDetail? {
        return stockDetails
            .filter { 
                it.dataType == dataType && 
                it.dataQuality in listOf(DataQuality.EXCELLENT, DataQuality.GOOD) 
            }
            .maxByOrNull { it.requestTimestamp }
    }
    
    companion object {
        /**
         * 새로운 국내 종목 생성
         */
        fun create(
            stockCode: String,
            stockName: String,
            marketType: DomesticMarketType,
            sectorCode: String? = null,
            listingDate: LocalDate? = null,
            rawData: String? = null
        ): DomesticStock {
            require(stockCode.length == 6) { "종목코드는 6자리여야 합니다: $stockCode" }
            require(stockCode.matches(Regex("^[A-Z0-9]{6}$"))) { "종목코드 형식이 올바르지 않습니다: $stockCode" }
            require(stockName.isNotBlank()) { "종목명은 필수입니다" }
            
            return DomesticStock(
                stockCode = stockCode,
                stockName = stockName,
                marketType = marketType,
                sectorCode = sectorCode,
                listingDate = listingDate,
                rawData = rawData,
                isActive = true
            )
        }
        
        /**
         * KOSPI 종목 생성
         */
        fun createKospi(
            stockCode: String,
            stockName: String,
            sectorCode: String? = null,
            listingDate: LocalDate? = null
        ): DomesticStock {
            return create(
                stockCode = stockCode,
                stockName = stockName,
                marketType = DomesticMarketType.KOSPI,
                sectorCode = sectorCode,
                listingDate = listingDate
            )
        }
        
        /**
         * KOSDAQ 종목 생성
         */
        fun createKosdaq(
            stockCode: String,
            stockName: String,
            sectorCode: String? = null,
            listingDate: LocalDate? = null
        ): DomesticStock {
            return create(
                stockCode = stockCode,
                stockName = stockName,
                marketType = DomesticMarketType.KOSDAQ,
                sectorCode = sectorCode,
                listingDate = listingDate
            )
        }
    }
}

/**
 * 국내 시장 타입 열거형
 */
enum class DomesticMarketType {
    KOSPI,    // 코스피
    KOSDAQ    // 코스닥
}

/**
 * 주식 데이터 타입 열거형
 */
enum class StockDataType {
    PRICE,   // 현재가
    CHART,   // 차트 (OHLCV)
    INDEX    // 지수
}

/**
 * 데이터 품질 열거형
 */
enum class DataQuality {
    EXCELLENT,  // 우수
    GOOD,       // 양호
    FAIR,       // 보통
    POOR        // 불량
}