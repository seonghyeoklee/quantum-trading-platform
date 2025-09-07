package com.quantum.stock.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import org.hibernate.annotations.Comment
import org.hibernate.annotations.JdbcTypeCode
import org.hibernate.type.SqlTypes
import java.math.BigDecimal
import java.time.LocalDate
import java.time.LocalDateTime

/**
 * 해외주식상세정보 엔티티
 * 
 * 해외 종목의 가격, 차트, 거래 데이터 등 상세 정보를 관리하는 DDD 기반 엔티티
 */
@Entity
@Table(
    name = "overseas_stock_detail",
    indexes = [
        Index(name = "idx_overseas_data_symbol_date", columnList = "symbol, exchange, trade_date"),
        Index(name = "idx_overseas_data_symbol_type", columnList = "symbol, exchange, data_type, request_timestamp"),
        Index(name = "idx_overseas_data_timestamp", columnList = "request_timestamp"),
        Index(name = "idx_overseas_data_endpoint", columnList = "api_endpoint, request_timestamp")
    ]
)
@Comment("해외주식상세정보 - 해외 종목의 가격/차트 데이터 (DDD 설계)")
class OverseasStockDetail(
    /**
     * 종목 심볼 (외래키)
     */
    @Column(name = "symbol", nullable = false, length = 10)
    @Comment("종목 심볼 (overseas_stocks 참조)")
    var symbol: String = "",
    
    /**
     * 거래소 (외래키)
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "exchange", nullable = false, length = 10)
    @Comment("거래소 (overseas_stocks 참조)")
    var exchange: OverseasExchange = OverseasExchange.NAS,
    
    /**
     * 데이터 타입
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "data_type", nullable = false, length = 20)
    @Comment("데이터 타입: price(현재가), chart(차트), index(지수)")
    var dataType: StockDataType = StockDataType.PRICE,
    
    /**
     * 사용된 KIS API 엔드포인트
     */
    @Column(name = "api_endpoint", nullable = false, length = 100)
    @Comment("사용된 KIS API 엔드포인트")
    var apiEndpoint: String = "",
    
    /**
     * API 호출 시간
     */
    @Column(name = "request_timestamp", nullable = false)
    @Comment("API 호출 시간 (KST)")
    var requestTimestamp: LocalDateTime = LocalDateTime.now(),
    
    /**
     * KIS API 완전한 원시 JSON 응답
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "raw_response", nullable = false, columnDefinition = "jsonb")
    @Comment("KIS API 완전한 원시 JSON 응답")
    var rawResponse: MutableMap<String, Any> = mutableMapOf(),
    
    /**
     * API 요청 파라미터
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "request_params", columnDefinition = "jsonb")
    @Comment("API 요청 파라미터")
    var requestParams: MutableMap<String, Any>? = null,
    
    /**
     * 응답 코드 (빠른 조회용)
     */
    @Column(name = "response_code", length = 10)
    @Comment("rt_cd (0: 성공, 기타: 오류)")
    var responseCode: String? = null,
    
    /**
     * 현재가 (USD, 소수점 포함)
     */
    @Column(name = "current_price", precision = 15, scale = 2)
    @Comment("현재가 USD (빠른 조회용)")
    var currentPrice: BigDecimal? = null,
    
    /**
     * 거래일
     */
    @Column(name = "trade_date")
    @Comment("거래일 (차트 데이터의 경우)")
    var tradeDate: LocalDate? = null,
    
    /**
     * 거래량
     */
    @Column(name = "volume")
    @Comment("거래량")
    var volume: Long? = null,
    
    /**
     * 데이터 품질
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "data_quality", length = 20)
    @Comment("데이터 품질 추적")
    var dataQuality: DataQuality = DataQuality.GOOD

) : BaseEntity() {
    
    /**
     * JPA를 위한 기본 생성자
     */
    protected constructor() : this(
        symbol = "",
        exchange = OverseasExchange.NAS,
        apiEndpoint = "",
        dataType = StockDataType.PRICE,
        requestTimestamp = LocalDateTime.now(),
        rawResponse = mutableMapOf()
    )
    
    /**
     * 해외주식종목과의 연관관계
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumns(
        JoinColumn(
            name = "symbol",
            referencedColumnName = "symbol",
            insertable = false,
            updatable = false
        ),
        JoinColumn(
            name = "exchange",
            referencedColumnName = "exchange",
            insertable = false,
            updatable = false
        ),
        foreignKey = ForeignKey(name = "fk_overseas_stock_detail_symbol_exchange")
    )
    var overseasStock: OverseasStock? = null
    
    /**
     * 성공적인 응답인지 확인
     */
    fun isSuccessful(): Boolean {
        return responseCode == "0"
    }
    
    /**
     * 현재가 데이터인지 확인
     */
    fun isPriceData(): Boolean {
        return dataType == StockDataType.PRICE
    }
    
    /**
     * 차트 데이터인지 확인
     */
    fun isChartData(): Boolean {
        return dataType == StockDataType.CHART
    }
    
    /**
     * 지수 데이터인지 확인
     */
    fun isIndexData(): Boolean {
        return dataType == StockDataType.INDEX
    }
    
    /**
     * 미국 시장 데이터인지 확인
     */
    fun isUsMarket(): Boolean {
        return exchange in listOf(OverseasExchange.NAS, OverseasExchange.NYS)
    }
    
    /**
     * 홍콩 시장 데이터인지 확인
     */
    fun isHongKongMarket(): Boolean {
        return exchange == OverseasExchange.HKS
    }
    
    /**
     * 양질의 데이터인지 확인
     */
    fun isGoodQuality(): Boolean {
        return dataQuality in listOf(DataQuality.EXCELLENT, DataQuality.GOOD)
    }
    
    /**
     * raw_response에서 특정 필드 추출
     */
    fun extractFromResponse(path: String): Any? {
        val pathParts = path.split(".")
        var current: Any? = rawResponse
        
        for (part in pathParts) {
            current = when (current) {
                is Map<*, *> -> current[part]
                else -> null
            }
            if (current == null) break
        }
        
        return current
    }
    
    /**
     * 전일대비 정보 추출 (현재가 데이터용)
     */
    fun getPriceChange(): String? {
        return extractFromResponse("output.diff") as? String
    }
    
    /**
     * 전일대비율 정보 추출 (현재가 데이터용)
     */
    fun getPriceChangeRate(): String? {
        return extractFromResponse("output.rate") as? String
    }
    
    /**
     * 차트 데이터 리스트 추출 (차트 데이터용)
     */
    @Suppress("UNCHECKED_CAST")
    fun getChartDataList(): List<Map<String, Any>>? {
        return extractFromResponse("output2") as? List<Map<String, Any>>
    }
    
    /**
     * 시가 추출 (차트 데이터용)
     */
    fun getOpenPrice(): BigDecimal? {
        return if (isChartData()) {
            getChartDataList()?.firstOrNull()?.let { firstRecord ->
                (firstRecord["open"] as? String)?.toBigDecimalOrNull()
                    ?: (firstRecord["open"] as? Number)?.let { BigDecimal(it.toString()) }
            }
        } else {
            null
        }
    }
    
    /**
     * 고가 추출 (차트 데이터용)
     */
    fun getHighPrice(): BigDecimal? {
        return if (isChartData()) {
            getChartDataList()?.firstOrNull()?.let { firstRecord ->
                (firstRecord["high"] as? String)?.toBigDecimalOrNull()
                    ?: (firstRecord["high"] as? Number)?.let { BigDecimal(it.toString()) }
            }
        } else {
            null
        }
    }
    
    /**
     * 저가 추출 (차트 데이터용)
     */
    fun getLowPrice(): BigDecimal? {
        return if (isChartData()) {
            getChartDataList()?.firstOrNull()?.let { firstRecord ->
                (firstRecord["low"] as? String)?.toBigDecimalOrNull()
                    ?: (firstRecord["low"] as? Number)?.let { BigDecimal(it.toString()) }
            }
        } else {
            null
        }
    }
    
    /**
     * 종가 추출 (차트 데이터용)
     */
    fun getClosePrice(): BigDecimal? {
        return if (isChartData()) {
            getChartDataList()?.firstOrNull()?.let { firstRecord ->
                (firstRecord["close"] as? String)?.toBigDecimalOrNull()
                    ?: (firstRecord["close"] as? Number)?.let { BigDecimal(it.toString()) }
            }
        } else {
            currentPrice
        }
    }
    
    /**
     * OHLCV 데이터 추출 (차트 데이터용)
     */
    data class OhlcvData(
        val date: LocalDate?,
        val open: BigDecimal?,
        val high: BigDecimal?,
        val low: BigDecimal?,
        val close: BigDecimal?,
        val volume: Long?
    )
    
    fun getOhlcvData(): OhlcvData {
        return OhlcvData(
            date = tradeDate,
            open = getOpenPrice(),
            high = getHighPrice(),
            low = getLowPrice(),
            close = getClosePrice(),
            volume = volume
        )
    }
    
    /**
     * 현재가를 한국 원화로 변환 (대략적인 환율 적용)
     */
    fun getCurrentPriceInKrw(exchangeRate: BigDecimal = BigDecimal("1300")): BigDecimal? {
        return currentPrice?.multiply(exchangeRate)
    }
    
    /**
     * 데이터 요약 정보 생성
     */
    fun getSummary(): String {
        val status = if (isSuccessful()) "SUCCESS" else "ERROR"
        val qualityInfo = "${dataType.name.lowercase()}/${dataQuality.name.lowercase()}"
        val priceInfo = currentPrice?.let { "$${String.format("%.2f", it)}" } ?: "N/A"
        return "$symbol@${exchange.name} [$qualityInfo] $priceInfo -> $status (${tradeDate ?: requestTimestamp.toLocalDate()})"
    }
    
    /**
     * 데이터 품질 업데이트
     */
    fun updateDataQuality(quality: DataQuality) {
        this.dataQuality = quality
    }
    
    /**
     * 현재가 정보 업데이트 (현재가 데이터 수신 시)
     */
    fun updatePriceInfo(currentPrice: BigDecimal?, volume: Long?) {
        this.currentPrice = currentPrice
        this.volume = volume
        this.tradeDate = LocalDate.now()
    }
    
    /**
     * 차트 정보 업데이트 (차트 데이터 수신 시)
     */
    fun updateChartInfo(tradeDate: LocalDate?, closePrice: BigDecimal?, volume: Long?) {
        this.tradeDate = tradeDate
        this.currentPrice = closePrice
        this.volume = volume
    }
    
    companion object {
        /**
         * 현재가 데이터 생성
         */
        fun createPriceData(
            symbol: String,
            exchange: OverseasExchange,
            apiEndpoint: String,
            rawResponse: Map<String, Any>,
            requestParams: Map<String, Any>? = null
        ): OverseasStockDetail {
            val detail = OverseasStockDetail(
                symbol = symbol,
                exchange = exchange,
                apiEndpoint = apiEndpoint,
                dataType = StockDataType.PRICE,
                rawResponse = rawResponse.toMutableMap(),
                requestParams = requestParams?.toMutableMap()
            )
            
            // 응답에서 주요 필드 추출
            detail.responseCode = rawResponse["rt_cd"] as? String
            
            val output = rawResponse["output"] as? Map<*, *>
            if (output != null) {
                // 해외 주식은 소수점이 있을 수 있음
                detail.currentPrice = (output["last"] as? String)?.toBigDecimalOrNull()
                    ?: (output["price"] as? Number)?.let { BigDecimal(it.toString()) }
                detail.volume = (output["tvol"] as? String)?.toLongOrNull()
                    ?: (output["volume"] as? Number)?.toLong()
                detail.tradeDate = LocalDate.now()
            }
            
            return detail
        }
        
        /**
         * 차트 데이터 생성
         */
        fun createChartData(
            symbol: String,
            exchange: OverseasExchange,
            apiEndpoint: String,
            rawResponse: Map<String, Any>,
            requestParams: Map<String, Any>? = null
        ): OverseasStockDetail {
            val detail = OverseasStockDetail(
                symbol = symbol,
                exchange = exchange,
                apiEndpoint = apiEndpoint,
                dataType = StockDataType.CHART,
                rawResponse = rawResponse.toMutableMap(),
                requestParams = requestParams?.toMutableMap()
            )
            
            // 응답에서 주요 필드 추출
            detail.responseCode = rawResponse["rt_cd"] as? String
            
            // 차트 데이터의 첫 번째 레코드에서 정보 추출
            val chartList = rawResponse["output2"] as? List<*>
            if (!chartList.isNullOrEmpty()) {
                val firstRecord = chartList[0] as? Map<*, *>
                if (firstRecord != null) {
                    detail.currentPrice = (firstRecord["close"] as? String)?.toBigDecimalOrNull()
                        ?: (firstRecord["close"] as? Number)?.let { BigDecimal(it.toString()) }
                    detail.volume = (firstRecord["tvol"] as? String)?.toLongOrNull()
                        ?: (firstRecord["volume"] as? Number)?.toLong()
                    detail.tradeDate = (firstRecord["xymd"] as? String)?.let { dateStr ->
                        if (dateStr.length == 8) {
                            LocalDate.of(
                                dateStr.substring(0, 4).toInt(),
                                dateStr.substring(4, 6).toInt(),
                                dateStr.substring(6, 8).toInt()
                            )
                        } else null
                    }
                }
            }
            
            return detail
        }
        
        /**
         * 지수 데이터 생성
         */
        fun createIndexData(
            symbol: String,
            exchange: OverseasExchange,
            apiEndpoint: String,
            rawResponse: Map<String, Any>,
            requestParams: Map<String, Any>? = null
        ): OverseasStockDetail {
            return OverseasStockDetail(
                symbol = symbol,
                exchange = exchange,
                apiEndpoint = apiEndpoint,
                dataType = StockDataType.INDEX,
                rawResponse = rawResponse.toMutableMap(),
                requestParams = requestParams?.toMutableMap()
            ).apply {
                responseCode = rawResponse["rt_cd"] as? String
                tradeDate = LocalDate.now()
            }
        }
    }
}