package com.quantum.stock.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import org.hibernate.annotations.Comment
import java.math.BigDecimal

/**
 * 해외주식종목 엔티티
 * 
 * NYSE/NASDAQ 등 해외 상장 종목의 기본 정보를 관리하는 DDD 기반 엔티티
 */
@Entity
@Table(
    name = "overseas_stocks",
    indexes = [
        Index(name = "idx_overseas_stocks_symbol", columnList = "symbol"),
        Index(name = "idx_overseas_stocks_exchange", columnList = "exchange"),
        Index(name = "idx_overseas_stocks_name_eng", columnList = "stock_name_eng"),
        Index(name = "idx_overseas_stocks_active", columnList = "is_active"),
        Index(name = "idx_overseas_stocks_symbol_exchange", columnList = "symbol, exchange")
    ],
    uniqueConstraints = [
        UniqueConstraint(name = "uk_overseas_symbol_exchange", columnNames = ["symbol", "exchange"])
    ]
)
@Comment("해외주식종목 - NYSE/NASDAQ 등 해외 상장 종목 정보 (DDD 설계)")
class OverseasStock(
    /**
     * 종목 심볼
     */
    @Column(name = "symbol", nullable = false, length = 10)
    @Comment("종목 심볼 (AAPL, MSFT 등)")
    var symbol: String = "",
    
    /**
     * 종목명 (영어)
     */
    @Column(name = "stock_name_eng", nullable = false, length = 200)
    @Comment("종목명 영어 (Apple Inc.)")
    var stockNameEng: String = "",
    
    /**
     * 종목명 (한국어)
     */
    @Column(name = "stock_name_kor", length = 200)
    @Comment("종목명 한국어 (애플)")
    var stockNameKor: String? = null,
    
    /**
     * 거래소
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "exchange", nullable = false, length = 10)
    @Comment("거래소 (NAS, NYS, HKS 등)")
    var exchange: OverseasExchange = OverseasExchange.NAS,
    
    /**
     * 국가코드
     */
    @Column(name = "country_code", nullable = false, length = 3)
    @Comment("국가코드 (US, HK, JP 등)")
    var countryCode: String = "US",
    
    /**
     * 통화
     */
    @Column(name = "currency", nullable = false, length = 3)
    @Comment("통화 (USD, HKD, JPY 등)")
    var currency: String = "USD",
    
    /**
     * 종목타입
     */
    @Column(name = "stock_type", length = 2)
    @Comment("종목타입 (2: 주식, 3: ETF)")
    var stockType: String? = null,
    
    /**
     * 섹터코드
     */
    @Column(name = "sector_code", length = 3)
    @Comment("섹터코드")
    var sectorCode: String? = null,
    
    /**
     * 호가단위
     */
    @Column(name = "tick_size", precision = 10, scale = 4)
    @Comment("호가단위")
    var tickSize: BigDecimal? = null,
    
    /**
     * 거래단위
     */
    @Column(name = "lot_size")
    @Comment("거래단위")
    var lotSize: Int = 1,
    
    /**
     * 거래시작시간 (HHMM)
     */
    @Column(name = "trading_start_time", length = 4)
    @Comment("거래시작시간 (HHMM)")
    var tradingStartTime: String? = null,
    
    /**
     * 거래종료시간 (HHMM)
     */
    @Column(name = "trading_end_time", length = 4)
    @Comment("거래종료시간 (HHMM)")
    var tradingEndTime: String? = null,
    
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
        symbol = "",
        stockNameEng = "",
        exchange = OverseasExchange.NAS
    )
    
    /**
     * 종목 상세정보와의 연관관계
     */
    @OneToMany(
        mappedBy = "overseasStock",
        cascade = [CascadeType.ALL],
        fetch = FetchType.LAZY
    )
    var stockDetails: MutableList<OverseasStockDetail> = mutableListOf()
    
    /**
     * NASDAQ 종목인지 확인
     */
    fun isNasdaq(): Boolean {
        return exchange == OverseasExchange.NAS
    }
    
    /**
     * NYSE 종목인지 확인
     */
    fun isNyse(): Boolean {
        return exchange == OverseasExchange.NYS
    }
    
    /**
     * 홍콩 거래소 종목인지 확인
     */
    fun isHongKong(): Boolean {
        return exchange == OverseasExchange.HKS
    }
    
    /**
     * 미국 시장 종목인지 확인
     */
    fun isUsMarket(): Boolean {
        return countryCode == "US"
    }
    
    /**
     * USD 통화인지 확인
     */
    fun isUsdCurrency(): Boolean {
        return currency == "USD"
    }
    
    /**
     * ETF인지 확인
     */
    fun isEtf(): Boolean {
        return stockType == "3"
    }
    
    /**
     * 주식인지 확인
     */
    fun isStock(): Boolean {
        return stockType == "2"
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
        stockNameEng: String? = null,
        stockNameKor: String? = null,
        exchange: OverseasExchange? = null,
        sectorCode: String? = null,
        tickSize: BigDecimal? = null,
        lotSize: Int? = null
    ) {
        stockNameEng?.let { this.stockNameEng = it }
        stockNameKor?.let { this.stockNameKor = it }
        exchange?.let { this.exchange = it }
        sectorCode?.let { this.sectorCode = it }
        tickSize?.let { this.tickSize = it }
        lotSize?.let { this.lotSize = it }
    }
    
    /**
     * 종목 표시명 가져오기 (한국어 우선)
     */
    fun getDisplayName(): String {
        return stockNameKor?.takeIf { it.isNotBlank() } ?: stockNameEng
    }
    
    /**
     * 종목 요약 정보 생성
     */
    fun getSummary(): String {
        val status = if (isActive) "활성" else "비활성"
        val displayName = getDisplayName()
        return "$symbol ($displayName) [${exchange.name}] - $status"
    }
    
    /**
     * 거래 시간대 정보
     */
    fun getTradingTimeInfo(): String? {
        return if (tradingStartTime != null && tradingEndTime != null) {
            "$tradingStartTime-$tradingEndTime"
        } else null
    }
    
    /**
     * 최신 주식 상세정보 조회
     */
    fun getLatestDetail(): OverseasStockDetail? {
        return stockDetails
            .filter { it.dataQuality in listOf(DataQuality.EXCELLENT, DataQuality.GOOD) }
            .maxByOrNull { it.requestTimestamp }
    }
    
    /**
     * 특정 타입의 최신 상세정보 조회
     */
    fun getLatestDetailByType(dataType: StockDataType): OverseasStockDetail? {
        return stockDetails
            .filter { 
                it.dataType == dataType && 
                it.dataQuality in listOf(DataQuality.EXCELLENT, DataQuality.GOOD) 
            }
            .maxByOrNull { it.requestTimestamp }
    }
    
    companion object {
        /**
         * 새로운 해외 종목 생성
         */
        fun create(
            symbol: String,
            stockNameEng: String,
            exchange: OverseasExchange,
            countryCode: String = "US",
            currency: String = "USD",
            stockNameKor: String? = null,
            stockType: String? = null,
            sectorCode: String? = null,
            tickSize: BigDecimal? = null,
            lotSize: Int = 1,
            rawData: String? = null
        ): OverseasStock {
            require(symbol.isNotBlank()) { "종목 심볼은 필수입니다" }
            require(symbol.matches(Regex("^[A-Z0-9.-]+$"))) { "종목 심볼 형식이 올바르지 않습니다: $symbol" }
            require(stockNameEng.isNotBlank()) { "영어 종목명은 필수입니다" }
            
            return OverseasStock(
                symbol = symbol,
                stockNameEng = stockNameEng,
                stockNameKor = stockNameKor,
                exchange = exchange,
                countryCode = countryCode,
                currency = currency,
                stockType = stockType,
                sectorCode = sectorCode,
                tickSize = tickSize,
                lotSize = lotSize,
                rawData = rawData,
                isActive = true
            )
        }
        
        /**
         * NASDAQ 종목 생성
         */
        fun createNasdaq(
            symbol: String,
            stockNameEng: String,
            stockNameKor: String? = null,
            stockType: String? = null,
            sectorCode: String? = null
        ): OverseasStock {
            return create(
                symbol = symbol,
                stockNameEng = stockNameEng,
                exchange = OverseasExchange.NAS,
                stockNameKor = stockNameKor,
                stockType = stockType,
                sectorCode = sectorCode
            )
        }
        
        /**
         * NYSE 종목 생성
         */
        fun createNyse(
            symbol: String,
            stockNameEng: String,
            stockNameKor: String? = null,
            stockType: String? = null,
            sectorCode: String? = null
        ): OverseasStock {
            return create(
                symbol = symbol,
                stockNameEng = stockNameEng,
                exchange = OverseasExchange.NYS,
                stockNameKor = stockNameKor,
                stockType = stockType,
                sectorCode = sectorCode
            )
        }
        
        /**
         * 홍콩 거래소 종목 생성
         */
        fun createHongKong(
            symbol: String,
            stockNameEng: String,
            stockNameKor: String? = null,
            stockType: String? = null
        ): OverseasStock {
            return create(
                symbol = symbol,
                stockNameEng = stockNameEng,
                exchange = OverseasExchange.HKS,
                countryCode = "HK",
                currency = "HKD",
                stockNameKor = stockNameKor,
                stockType = stockType
            )
        }
    }
}

/**
 * 해외 거래소 열거형
 */
enum class OverseasExchange {
    NAS,    // NASDAQ
    NYS,    // NYSE (New York Stock Exchange)
    HKS,    // Hong Kong Stock Exchange
    TSE,    // Tokyo Stock Exchange
    SHS,    // Shanghai Stock Exchange
    SZS     // Shenzhen Stock Exchange
}