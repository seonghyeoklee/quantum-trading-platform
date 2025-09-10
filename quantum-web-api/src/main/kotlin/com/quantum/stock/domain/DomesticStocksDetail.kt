package com.quantum.stock.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import org.hibernate.annotations.Comment
import org.hibernate.annotations.JdbcTypeCode
import org.hibernate.type.SqlTypes
import java.time.LocalDate
import java.time.LocalDateTime

/**
 * 국내주식상세정보 엔티티
 * 
 * 국내 종목의 가격, 차트, 거래 데이터 등 상세 정보를 관리하는 DDD 기반 엔티티
 */
@Entity
@Table(
    name = "domestic_stocks_detail",
    indexes = [
        Index(name = "idx_domestic_data_stock_date", columnList = "stock_code, trade_date"),
        Index(name = "idx_domestic_data_stock_type", columnList = "stock_code, data_type, request_timestamp"),
        Index(name = "idx_domestic_data_timestamp", columnList = "request_timestamp"),
        Index(name = "idx_domestic_data_endpoint", columnList = "api_endpoint, request_timestamp")
    ]
)
@Comment("국내주식상세정보 - 국내 종목의 가격/차트 데이터 (DDD 설계)")
class DomesticStocksDetail(
    /**
     * 종목코드 (외래키)
     */
    @Column(name = "stock_code", nullable = false, length = 6)
    @Comment("종목코드 (domestic_stocks 참조)")
    var stockCode: String = "",
    
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
     * 현재가 (빠른 조회용)
     */
    @Column(name = "current_price")
    @Comment("현재가 (빠른 조회용)")
    var currentPrice: Long? = null,
    
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
        stockCode = "",
        apiEndpoint = "",
        dataType = StockDataType.PRICE,
        requestTimestamp = LocalDateTime.now(),
        rawResponse = mutableMapOf()
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
        foreignKey = ForeignKey(name = "fk_domestic_stock_detail_stock_code")
    )
    var domesticStock: DomesticStock? = null
    
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
        return extractFromResponse("output.prdy_vrss") as? String
    }
    
    /**
     * 전일대비율 정보 추출 (현재가 데이터용)
     */
    fun getPriceChangeRate(): String? {
        return extractFromResponse("output.prdy_ctrt") as? String
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
    fun getOpenPrice(): Long? {
        return if (isChartData()) {
            // 새로운 ohlcv 구조에서 추출
            val ohlcvData = extractFromResponse("ohlcv") as? Map<*, *>
            ohlcvData?.let { ohlcv ->
                (ohlcv["open"] as? Number)?.toLong()
            } ?: run {
                // 기존 구조 fallback
                getChartDataList()?.firstOrNull()?.let { firstRecord ->
                    (firstRecord["stck_oprc"] as? String)?.toLongOrNull()
                }
            }
        } else {
            null
        }
    }
    
    /**
     * 고가 추출 (차트 데이터용)
     */
    fun getHighPrice(): Long? {
        return if (isChartData()) {
            // 새로운 ohlcv 구조에서 추출
            val ohlcvData = extractFromResponse("ohlcv") as? Map<*, *>
            ohlcvData?.let { ohlcv ->
                (ohlcv["high"] as? Number)?.toLong()
            } ?: run {
                // 기존 구조 fallback
                getChartDataList()?.firstOrNull()?.let { firstRecord ->
                    (firstRecord["stck_hgpr"] as? String)?.toLongOrNull()
                }
            }
        } else {
            null
        }
    }
    
    /**
     * 저가 추출 (차트 데이터용)
     */
    fun getLowPrice(): Long? {
        return if (isChartData()) {
            // 새로운 ohlcv 구조에서 추출
            val ohlcvData = extractFromResponse("ohlcv") as? Map<*, *>
            ohlcvData?.let { ohlcv ->
                (ohlcv["low"] as? Number)?.toLong()
            } ?: run {
                // 기존 구조 fallback
                getChartDataList()?.firstOrNull()?.let { firstRecord ->
                    (firstRecord["stck_lwpr"] as? String)?.toLongOrNull()
                }
            }
        } else {
            null
        }
    }
    
    /**
     * 종가 추출 (차트 데이터용)
     */
    fun getClosePrice(): Long? {
        return if (isChartData()) {
            // 새로운 ohlcv 구조에서 추출
            val ohlcvData = extractFromResponse("ohlcv") as? Map<*, *>
            ohlcvData?.let { ohlcv ->
                (ohlcv["close"] as? Number)?.toLong()
            } ?: run {
                // 기존 구조 fallback
                getChartDataList()?.firstOrNull()?.let { firstRecord ->
                    (firstRecord["stck_clpr"] as? String)?.toLongOrNull()
                }
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
        val open: Long?,
        val high: Long?,
        val low: Long?,
        val close: Long?,
        val volume: Long?
    )
    
    fun getOhlcvData(): OhlcvData {
        // volume을 ohlcv 구조에서도 시도해보기
        val volumeValue = if (isChartData()) {
            val ohlcvData = extractFromResponse("ohlcv") as? Map<*, *>
            ohlcvData?.let { ohlcv ->
                (ohlcv["volume"] as? Number)?.toLong()
            } ?: volume
        } else {
            volume
        }
        
        return OhlcvData(
            date = tradeDate,
            open = getOpenPrice(),
            high = getHighPrice(),
            low = getLowPrice(),
            close = getClosePrice(),
            volume = volumeValue
        )
    }
    
    /**
     * 데이터 요약 정보 생성
     */
    fun getSummary(): String {
        val status = if (isSuccessful()) "SUCCESS" else "ERROR"
        val qualityInfo = "${dataType.name.lowercase()}/${dataQuality.name.lowercase()}"
        val priceInfo = currentPrice?.let { "₩${String.format("%,d", it)}" } ?: "N/A"
        return "$stockCode [$qualityInfo] $priceInfo -> $status (${tradeDate ?: requestTimestamp.toLocalDate()})"
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
    fun updatePriceInfo(currentPrice: Long?, volume: Long?) {
        this.currentPrice = currentPrice
        this.volume = volume
        this.tradeDate = LocalDate.now()
    }
    
    /**
     * 차트 정보 업데이트 (차트 데이터 수신 시)
     */
    fun updateChartInfo(tradeDate: LocalDate?, closePrice: Long?, volume: Long?) {
        this.tradeDate = tradeDate
        this.currentPrice = closePrice
        this.volume = volume
    }
    
    companion object {
        /**
         * 현재가 데이터 생성
         */
        fun createPriceData(
            stockCode: String,
            apiEndpoint: String,
            rawResponse: Map<String, Any>,
            requestParams: Map<String, Any>? = null
        ): DomesticStocksDetail {
            val detail = DomesticStocksDetail(
                stockCode = stockCode,
                apiEndpoint = apiEndpoint,
                dataType = StockDataType.PRICE,
                rawResponse = rawResponse.toMutableMap(),
                requestParams = requestParams?.toMutableMap()
            )
            
            // 응답에서 주요 필드 추출
            detail.responseCode = rawResponse["rt_cd"] as? String
            
            val output = rawResponse["output"] as? Map<*, *>
            if (output != null) {
                detail.currentPrice = (output["stck_prpr"] as? String)?.toLongOrNull()
                detail.volume = (output["acml_vol"] as? String)?.toLongOrNull()
                detail.tradeDate = LocalDate.now()
            }
            
            return detail
        }
        
        /**
         * 차트 데이터 생성
         */
        fun createChartData(
            stockCode: String,
            apiEndpoint: String,
            rawResponse: Map<String, Any>,
            requestParams: Map<String, Any>? = null
        ): DomesticStocksDetail {
            val detail = DomesticStocksDetail(
                stockCode = stockCode,
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
                    detail.currentPrice = (firstRecord["stck_clpr"] as? String)?.toLongOrNull()
                    detail.volume = (firstRecord["acml_vol"] as? String)?.toLongOrNull()
                    detail.tradeDate = (firstRecord["stck_bsop_date"] as? String)?.let { dateStr ->
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
            stockCode: String,
            apiEndpoint: String,
            rawResponse: Map<String, Any>,
            requestParams: Map<String, Any>? = null
        ): DomesticStocksDetail {
            return DomesticStocksDetail(
                stockCode = stockCode,
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