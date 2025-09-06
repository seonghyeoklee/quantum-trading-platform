package com.quantum.kis.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import org.hibernate.annotations.Comment
import org.hibernate.annotations.JdbcTypeCode
import org.hibernate.type.SqlTypes
import java.time.LocalDate
import java.time.LocalDateTime

/**
 * KIS API 원시 시장 데이터
 * 
 * KIS OpenAPI의 모든 응답을 원본 그대로 저장하는 통합 저장소
 * 500+ 종목 대응을 위한 최적화된 인덱싱 제공
 */
@Entity
@Table(
    name = "kis_market_data",
    indexes = [
        Index(name = "idx_market_data_symbol_date", columnList = "symbol, trade_date"),
        Index(name = "idx_market_data_symbol_type", columnList = "symbol, data_type, request_timestamp"),
        Index(name = "idx_market_data_symbol_timestamp", columnList = "symbol, request_timestamp"),
        Index(name = "idx_market_data_endpoint", columnList = "api_endpoint, request_timestamp"),
        Index(name = "idx_market_data_type_date", columnList = "data_type, trade_date"),
        Index(name = "idx_market_data_symbol_type_date", columnList = "symbol, data_type, trade_date, request_timestamp"),
        Index(name = "idx_market_data_recent_data", columnList = "data_type, request_timestamp")
    ]
)
@Comment("KIS API 원시 시장 데이터 - 500+ 종목 지원")
class KisMarketData(
    // ========== 기본 식별 정보 (테이블 앞부분) ==========
    /**
     * 종목 코드 (005930=삼성전자, AAPL=애플 등)
     */
    @Column(name = "symbol", nullable = false, length = 20)
    @Comment("종목 코드")
    var symbol: String = "",
    
    /**
     * 데이터 타입
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "data_type", nullable = false, length = 20)
    @Comment("데이터 타입: price(현재가), chart(차트), index(지수)")
    var dataType: KisDataType = KisDataType.PRICE,
    
    /**
     * 시장 타입
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "market_type", nullable = false, length = 20)
    @Comment("시장 구분: domestic(국내), overseas(해외)")
    var marketType: KisMarketType = KisMarketType.DOMESTIC,
    
    /**
     * 사용된 KIS API 엔드포인트
     */
    @Column(name = "api_endpoint", nullable = false, length = 100)
    @Comment("KIS API 엔드포인트 경로")
    var apiEndpoint: String = "",
    
    /**
     * API 호출 시간
     */
    @Column(name = "request_timestamp", nullable = false)
    @Comment("KIS API 호출 시간")
    var requestTimestamp: LocalDateTime = LocalDateTime.now(),
    
    // ========== 응답 상태 정보 ==========
    /**
     * 응답 코드 (빠른 상태 확인용)
     */
    @Column(name = "response_code", length = 10)
    @Comment("KIS API 응답 코드 (0=성공)")
    var responseCode: String? = null,
    
    /**
     * 데이터 품질 등급
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "data_quality", length = 20)
    @Comment("데이터 품질 추적")
    var dataQuality: KisDataQuality = KisDataQuality.GOOD,
    
    // ========== 추출된 핵심 데이터 (빠른 조회용) ==========
    /**
     * 현재가 (빠른 조회용 추출 필드)
     */
    @Column(name = "current_price")
    @Comment("현재가 (빠른 조회를 위해 추출)")
    var currentPrice: Long? = null,
    
    /**
     * 거래량 (빠른 조회용)
     */
    @Column(name = "volume")
    @Comment("거래량 (빠른 조회용)")
    var volume: Long? = null,
    
    /**
     * 거래일 (차트 데이터용)
     */
    @Column(name = "trade_date")
    @Comment("거래일 (차트 데이터의 경우)")
    var tradeDate: LocalDate? = null,
    
    // ========== JSON 원시 데이터 (테이블 끝부분) ==========
    /**
     * API 요청 파라미터
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "request_params", columnDefinition = "jsonb")
    @Comment("API 요청 파라미터")
    var requestParams: MutableMap<String, Any>? = null,
    
    /**
     * KIS API 완전한 원시 JSON 응답
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "raw_response", nullable = false, columnDefinition = "jsonb")
    @Comment("KIS API 완전한 원시 JSON 응답 - 모든 데이터 보존")
    var rawResponse: MutableMap<String, Any> = mutableMapOf()

) : BaseEntity() {
    
    /**
     * JPA를 위한 기본 생성자
     */
    protected constructor() : this(
        symbol = "",
        apiEndpoint = "",
        dataType = KisDataType.PRICE,
        marketType = KisMarketType.DOMESTIC,
        requestTimestamp = LocalDateTime.now(),
        rawResponse = mutableMapOf()
    )
    
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
        return dataType == KisDataType.PRICE
    }
    
    /**
     * 차트 데이터인지 확인
     */
    fun isChartData(): Boolean {
        return dataType == KisDataType.CHART
    }
    
    /**
     * 국내 시장 데이터인지 확인
     */
    fun isDomesticMarket(): Boolean {
        return marketType == KisMarketType.DOMESTIC
    }
    
    /**
     * 해외 시장 데이터인지 확인
     */
    fun isOverseasMarket(): Boolean {
        return marketType == KisMarketType.OVERSEAS
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
     * 데이터 요약 정보 생성
     */
    fun getSummary(): String {
        val status = if (isSuccessful()) "SUCCESS" else "ERROR"
        val marketInfo = "${marketType.name.lowercase()}/${dataType.name.lowercase()}"
        return "$symbol [$marketInfo] -> $status (${tradeDate ?: requestTimestamp.toLocalDate()})"
    }
    
    companion object {
        /**
         * 현재가 데이터 생성
         */
        fun createPriceData(
            symbol: String,
            apiEndpoint: String,
            marketType: KisMarketType,
            rawResponse: Map<String, Any>,
            requestParams: Map<String, Any>? = null
        ): KisMarketData {
            val data = KisMarketData(
                symbol = symbol,
                apiEndpoint = apiEndpoint,
                dataType = KisDataType.PRICE,
                marketType = marketType,
                rawResponse = rawResponse.toMutableMap(),
                requestParams = requestParams?.toMutableMap()
            )
            
            // 응답에서 주요 필드 추출
            data.responseCode = rawResponse["rt_cd"] as? String
            
            val output = rawResponse["output"] as? Map<*, *>
            if (output != null) {
                data.currentPrice = (output["stck_prpr"] as? String)?.toLongOrNull()
                data.volume = (output["acml_vol"] as? String)?.toLongOrNull()
                data.tradeDate = LocalDate.now() // 현재가는 오늘 날짜
            }
            
            return data
        }
        
        /**
         * 차트 데이터 생성
         */
        fun createChartData(
            symbol: String,
            apiEndpoint: String,
            marketType: KisMarketType,
            rawResponse: Map<String, Any>,
            requestParams: Map<String, Any>? = null
        ): KisMarketData {
            val data = KisMarketData(
                symbol = symbol,
                apiEndpoint = apiEndpoint,
                dataType = KisDataType.CHART,
                marketType = marketType,
                rawResponse = rawResponse.toMutableMap(),
                requestParams = requestParams?.toMutableMap()
            )
            
            // 응답에서 주요 필드 추출
            data.responseCode = rawResponse["rt_cd"] as? String
            
            // 차트 데이터의 첫 번째 레코드에서 정보 추출
            val chartList = rawResponse["output2"] as? List<*>
            if (!chartList.isNullOrEmpty()) {
                val firstRecord = chartList[0] as? Map<*, *>
                if (firstRecord != null) {
                    data.currentPrice = (firstRecord["stck_clpr"] as? String)?.toLongOrNull() // 종가
                    data.volume = (firstRecord["acml_vol"] as? String)?.toLongOrNull()
                    data.tradeDate = (firstRecord["stck_bsop_date"] as? String)?.let { dateStr ->
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
            
            return data
        }
    }
}

/**
 * KIS 데이터 타입 열거형
 */
enum class KisDataType {
    PRICE,   // 현재가
    CHART,   // 차트 (OHLCV)
    INDEX    // 지수
}

/**
 * KIS 시장 타입 열거형  
 */
enum class KisMarketType {
    DOMESTIC,  // 국내
    OVERSEAS   // 해외
}

/**
 * KIS 데이터 품질 열거형
 */
enum class KisDataQuality {
    EXCELLENT,  // 우수
    GOOD,       // 양호
    FAIR,       // 보통
    POOR        // 불량
}