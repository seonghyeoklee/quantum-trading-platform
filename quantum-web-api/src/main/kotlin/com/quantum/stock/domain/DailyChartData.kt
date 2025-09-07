package com.quantum.stock.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import org.hibernate.annotations.Comment
import java.math.BigDecimal
import java.math.RoundingMode
import java.time.LocalDate

/**
 * 일봉 차트 데이터 엔티티 (차트/백테스팅 전용 최적화)
 * 
 * OHLCV 데이터를 위한 전용 최적화 테이블로, 백테스팅과 차트 구현에 최적화된 구조
 */
@Entity
@Table(
    name = "daily_chart_data",
    indexes = [
        Index(name = "idx_daily_chart_stock_code", columnList = "stock_code"),
        Index(name = "idx_daily_chart_trade_date", columnList = "trade_date"),
        Index(name = "idx_daily_chart_stock_date", columnList = "stock_code, trade_date DESC"),
        Index(name = "idx_daily_chart_close_price", columnList = "close_price"),
        Index(name = "idx_daily_chart_volume", columnList = "volume DESC")
    ],
    uniqueConstraints = [
        UniqueConstraint(name = "uk_daily_chart_stock_date", columnNames = ["stock_code", "trade_date"])
    ]
)
@Comment("일봉 차트 데이터 - 백테스팅 및 차트 구현용 전용 테이블")
class DailyChartData(
    /**
     * 종목코드 (6자리)
     */
    @Column(name = "stock_code", length = 6, nullable = false)
    @Comment("6자리 종목코드 (예: 005930=삼성전자)")
    val stockCode: String,
    
    /**
     * 거래일
     */
    @Column(name = "trade_date", nullable = false)
    @Comment("거래일 (주말/공휴일 제외)")
    val tradeDate: LocalDate,
    
    /**
     * 시가 (당일 시작가격)
     */
    @Column(name = "open_price", precision = 12, scale = 2, nullable = false)
    @Comment("시가 (당일 시작가격)")
    val openPrice: BigDecimal,
    
    /**
     * 고가 (당일 최고가격)
     */
    @Column(name = "high_price", precision = 12, scale = 2, nullable = false)
    @Comment("고가 (당일 최고가격)")
    val highPrice: BigDecimal,
    
    /**
     * 저가 (당일 최저가격)
     */
    @Column(name = "low_price", precision = 12, scale = 2, nullable = false)
    @Comment("저가 (당일 최저가격)")
    val lowPrice: BigDecimal,
    
    /**
     * 종가 (당일 마감가격/현재가)
     */
    @Column(name = "close_price", precision = 12, scale = 2, nullable = false)
    @Comment("종가 (당일 마감가격/현재가)")
    val closePrice: BigDecimal,
    
    /**
     * 거래량 (주식 수)
     */
    @Column(name = "volume", nullable = false)
    @Comment("거래량 (주식 수)")
    val volume: Long,
    
    /**
     * 거래대금 (원)
     */
    @Column(name = "amount", precision = 18, scale = 2)
    @Comment("거래대금 (원)")
    val amount: BigDecimal? = null,
    
    /**
     * 전일대비 가격변동
     */
    @Column(name = "price_change", precision = 12, scale = 2)
    @Comment("전일대비 가격변동")
    val priceChange: BigDecimal? = null,
    
    /**
     * 전일대비 변동률 (%)
     */
    @Column(name = "price_change_rate", precision = 8, scale = 4)
    @Comment("전일대비 변동률 (%)")
    val priceChangeRate: BigDecimal? = null,
    
    /**
     * 데이터 출처
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "data_source", length = 20)
    @Comment("데이터 출처")
    val dataSource: ChartDataSource = ChartDataSource.KIS_API,
    
    /**
     * 데이터 품질
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "data_quality", length = 20)
    @Comment("EXCELLENT: 완전한 OHLCV, GOOD: 일부 누락, POOR: 추정값")
    val dataQuality: DataQuality = DataQuality.GOOD

) : BaseEntity() {
    
    /**
     * JPA를 위한 기본 생성자
     */
    protected constructor() : this(
        stockCode = "",
        tradeDate = LocalDate.now(),
        openPrice = BigDecimal.ZERO,
        highPrice = BigDecimal.ZERO,
        lowPrice = BigDecimal.ZERO,
        closePrice = BigDecimal.ZERO,
        volume = 0L
    )
    
    /**
     * 국내주식종목과의 연관관계
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(
        name = "stock_code",
        referencedColumnName = "stock_code",
        insertable = false,
        updatable = false,
        foreignKey = ForeignKey(name = "fk_daily_chart_data_stock_code")
    )
    var stock: DomesticStock? = null
    
    /**
     * OHLC 관계가 올바른지 검증
     * Low ≤ Open/Close ≤ High
     */
    fun isValidOhlc(): Boolean {
        return lowPrice <= openPrice && 
               openPrice <= highPrice && 
               lowPrice <= closePrice && 
               closePrice <= highPrice
    }
    
    /**
     * 일일 수익률 계산 (종가 기준)
     */
    fun getDailyReturn(): BigDecimal? {
        return if (openPrice > BigDecimal.ZERO) {
            val change = closePrice - openPrice
            change.divide(openPrice, 6, RoundingMode.HALF_UP) * BigDecimal(100)
        } else null
    }
    
    /**
     * 일중 변동폭 계산 (고가-저가)
     */
    fun getDailyRange(): BigDecimal {
        return highPrice - lowPrice
    }
    
    /**
     * 일중 변동률 계산 (%)
     */
    fun getDailyRangeRate(): BigDecimal? {
        return if (lowPrice > BigDecimal.ZERO) {
            getDailyRange().divide(lowPrice, 6, RoundingMode.HALF_UP) * BigDecimal(100)
        } else null
    }
    
    /**
     * 평균가 계산 (OHLC 평균)
     */
    fun getTypicalPrice(): BigDecimal {
        return (highPrice + lowPrice + closePrice)
            .divide(BigDecimal(3), 2, RoundingMode.HALF_UP)
    }
    
    /**
     * 가중평균가 계산 ((H+L+C+C)/4)
     */
    fun getWeightedPrice(): BigDecimal {
        return (highPrice + lowPrice + closePrice + closePrice)
            .divide(BigDecimal(4), 2, RoundingMode.HALF_UP)
    }
    
    /**
     * 실체(몸통) 크기 계산 |Close - Open|
     */
    fun getBodySize(): BigDecimal {
        return (closePrice - openPrice).abs()
    }
    
    /**
     * 상단 꼬리 크기 계산
     */
    fun getUpperShadow(): BigDecimal {
        return highPrice - maxOf(openPrice, closePrice)
    }
    
    /**
     * 하단 꼬리 크기 계산
     */
    fun getLowerShadow(): BigDecimal {
        return minOf(openPrice, closePrice) - lowPrice
    }
    
    /**
     * 양봉인지 확인 (종가 > 시가)
     */
    fun isBullish(): Boolean {
        return closePrice > openPrice
    }
    
    /**
     * 음봉인지 확인 (종가 < 시가)
     */
    fun isBearish(): Boolean {
        return closePrice < openPrice
    }
    
    /**
     * 도지(십자형)인지 확인 (종가 ≈ 시가)
     */
    fun isDoji(threshold: BigDecimal = BigDecimal("0.001")): Boolean {
        val bodyRatio = if (closePrice > BigDecimal.ZERO) {
            getBodySize().divide(closePrice, 6, RoundingMode.HALF_UP)
        } else BigDecimal.ZERO
        
        return bodyRatio <= threshold
    }
    
    /**
     * 거래량 강도 계산 (거래량 / 평균 거래량 비교용)
     */
    fun getVolumeIntensity(averageVolume: Long): BigDecimal? {
        return if (averageVolume > 0) {
            BigDecimal(volume).divide(BigDecimal(averageVolume), 2, RoundingMode.HALF_UP)
        } else null
    }
    
    /**
     * 차트 데이터 요약 정보
     */
    fun getChartSummary(): String {
        val direction = when {
            isBullish() -> "▲"
            isBearish() -> "▼"
            else -> "="
        }
        val changeInfo = priceChange?.let { "($direction${it.abs()})" } ?: ""
        return "$stockCode $tradeDate: O$openPrice H$highPrice L$lowPrice C$closePrice V${String.format("%,d", volume)} $changeInfo"
    }
    
    /**
     * 백테스팅용 데이터 검증
     */
    fun isValidForBacktest(): Boolean {
        return isValidOhlc() && 
               volume >= 0 && 
               closePrice > BigDecimal.ZERO &&
               dataQuality in listOf(DataQuality.EXCELLENT, DataQuality.GOOD)
    }
    
    /**
     * 캔들스틱 패턴 분석을 위한 데이터 구조
     */
    data class CandlestickData(
        val date: LocalDate,
        val open: BigDecimal,
        val high: BigDecimal,
        val low: BigDecimal,
        val close: BigDecimal,
        val volume: Long,
        val bodySize: BigDecimal,
        val upperShadow: BigDecimal,
        val lowerShadow: BigDecimal,
        val isBullish: Boolean,
        val isDoji: Boolean
    )
    
    /**
     * 캔들스틱 분석용 데이터 반환
     */
    fun toCandlestickData(): CandlestickData {
        return CandlestickData(
            date = tradeDate,
            open = openPrice,
            high = highPrice,
            low = lowPrice,
            close = closePrice,
            volume = volume,
            bodySize = getBodySize(),
            upperShadow = getUpperShadow(),
            lowerShadow = getLowerShadow(),
            isBullish = isBullish(),
            isDoji = isDoji()
        )
    }
    
    companion object {
        /**
         * 새로운 차트 데이터 생성 (팩토리 메서드)
         */
        fun create(
            stockCode: String,
            tradeDate: LocalDate,
            openPrice: BigDecimal,
            highPrice: BigDecimal,
            lowPrice: BigDecimal,
            closePrice: BigDecimal,
            volume: Long,
            amount: BigDecimal? = null,
            priceChange: BigDecimal? = null,
            priceChangeRate: BigDecimal? = null,
            dataSource: ChartDataSource = ChartDataSource.KIS_API,
            dataQuality: DataQuality = DataQuality.GOOD
        ): DailyChartData {
            require(stockCode.length == 6) { "종목코드는 6자리여야 합니다: $stockCode" }
            require(stockCode.matches(Regex("^[A-Z0-9]{6}$"))) { "종목코드 형식이 올바르지 않습니다: $stockCode" }
            require(openPrice >= BigDecimal.ZERO) { "시가는 0 이상이어야 합니다" }
            require(highPrice >= BigDecimal.ZERO) { "고가는 0 이상이어야 합니다" }
            require(lowPrice >= BigDecimal.ZERO) { "저가는 0 이상이어야 합니다" }
            require(closePrice >= BigDecimal.ZERO) { "종가는 0 이상이어야 합니다" }
            require(volume >= 0) { "거래량은 0 이상이어야 합니다" }
            
            val chartData = DailyChartData(
                stockCode = stockCode,
                tradeDate = tradeDate,
                openPrice = openPrice,
                highPrice = highPrice,
                lowPrice = lowPrice,
                closePrice = closePrice,
                volume = volume,
                amount = amount,
                priceChange = priceChange,
                priceChangeRate = priceChangeRate,
                dataSource = dataSource,
                dataQuality = dataQuality
            )
            
            require(chartData.isValidOhlc()) { "OHLC 관계가 올바르지 않습니다: O$openPrice H$highPrice L$lowPrice C$closePrice" }
            
            return chartData
        }
        
        /**
         * ETL용 생성 메서드 (DomesticStockDetail에서 변환)
         */
        fun fromStockDetail(detail: DomesticStockDetail): DailyChartData? {
            if (!detail.isChartData() || detail.tradeDate == null) {
                return null
            }
            
            val ohlcv = detail.getOhlcvData()
            if (ohlcv.open == null || ohlcv.high == null || 
                ohlcv.low == null || ohlcv.close == null) {
                return null
            }
            
            return create(
                stockCode = detail.stockCode,
                tradeDate = detail.tradeDate!!,
                openPrice = BigDecimal(ohlcv.open!!),
                highPrice = BigDecimal(ohlcv.high!!),
                lowPrice = BigDecimal(ohlcv.low!!),
                closePrice = BigDecimal(ohlcv.close!!),
                volume = ohlcv.volume ?: 0L,
                dataQuality = detail.dataQuality,
                dataSource = ChartDataSource.KIS_API
            )
        }
    }
}

/**
 * 차트 데이터 출처 열거형
 */
enum class ChartDataSource {
    KIS_API,        // KIS Open API
    PYKRX,          // PyKRX 라이브러리
    YFINANCE,       // yfinance 라이브러리
    MANUAL          // 수동 입력
}