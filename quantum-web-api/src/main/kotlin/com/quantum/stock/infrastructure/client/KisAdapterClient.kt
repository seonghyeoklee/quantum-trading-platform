package com.quantum.stock.infrastructure.client

import com.fasterxml.jackson.annotation.JsonProperty
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpStatus
import org.springframework.stereotype.Component
import org.springframework.web.reactive.function.client.WebClient
import org.springframework.web.reactive.function.client.awaitBody
import org.springframework.web.server.ResponseStatusException
import java.time.LocalDateTime

/**
 * KIS Adapter 클라이언트
 * 
 * FastAPI로 구현된 KIS Adapter 서버와 통신하는 클라이언트
 * 포트 8000에서 실행되는 adapter.quantum-trading.com과 연동
 */
@Component
class KisAdapterClient(
    private val webClient: WebClient,
    @Value("\${kis.adapter.base-url:http://adapter.quantum-trading.com:8000}")
    private val adapterBaseUrl: String
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    /**
     * 국내 주식 상세 정보 조회
     * 
     * @param stockCode 종목코드 (예: 005930)
     * @return KIS API로부터 받은 상세 정보
     */
    suspend fun getDomesticStockDetail(stockCode: String): KisStockDetailResponse {
        logger.info("KIS Adapter에서 주식 상세 정보 조회 - stockCode: $stockCode")
        
        return try {
            val response = webClient
                .get()
                .uri("$adapterBaseUrl/domestic/price/$stockCode")
                .retrieve()
                .onStatus({ it.is4xxClientError }) { 
                    throw ResponseStatusException(HttpStatus.NOT_FOUND, "종목을 찾을 수 없습니다: $stockCode")
                }
                .onStatus({ it.is5xxServerError }) {
                    throw ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "KIS API 서버 오류")
                }
                .awaitBody<KisStockDetailResponse>()
            
            logger.info("주식 상세 정보 조회 완료 - $stockCode")
            response
            
        } catch (exception: Exception) {
            logger.error("주식 상세 정보 조회 실패 - $stockCode", exception)
            throw when (exception) {
                is ResponseStatusException -> exception
                else -> ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "KIS Adapter 통신 실패: ${exception.message}")
            }
        }
    }
    
    /**
     * KIS Adapter 서버 상태 확인
     */
    suspend fun checkAdapterHealth(): AdapterHealthResponse {
        logger.debug("KIS Adapter 서버 상태 확인")
        
        return try {
            val startTime = System.currentTimeMillis()
            
            val response = webClient
                .get()
                .uri("$adapterBaseUrl/health")
                .retrieve()
                .awaitBody<Map<String, Any>>()
            
            val responseTime = System.currentTimeMillis() - startTime
            
            AdapterHealthResponse(
                isHealthy = true,
                responseTimeMs = responseTime,
                checkedAt = LocalDateTime.now(),
                serverInfo = response
            )
            
        } catch (exception: Exception) {
            logger.warn("KIS Adapter 서버 상태 확인 실패", exception)
            AdapterHealthResponse(
                isHealthy = false,
                responseTimeMs = -1,
                checkedAt = LocalDateTime.now(),
                error = exception.message
            )
        }
    }
}

/**
 * KIS 주식 상세 정보 응답 DTO
 * 
 * KIS Adapter에서 받는 JSON 응답 구조에 맞춤
 */
data class KisStockDetailResponse(
    @JsonProperty("rt_cd") val rtCd: String,           // 응답코드
    @JsonProperty("msg_cd") val msgCd: String,         // 메시지코드
    @JsonProperty("msg1") val msg1: String,            // 메시지
    val output: KisStockOutput,                        // 실제 데이터
    @JsonProperty("data_source") val dataSource: String, // 데이터 소스
    val timestamp: String                              // 타임스탬프
)

/**
 * KIS 주식 상세 정보 (output 부분)
 */
data class KisStockOutput(
    // === 현재가 정보 ===
    @JsonProperty("stck_prpr") val currentPrice: String,           // 주식 현재가
    @JsonProperty("prdy_vrss") val previousDayChange: String,      // 전일 대비
    @JsonProperty("prdy_vrss_sign") val changeSign: String,        // 전일 대비 부호 (1:상승, 2:상승, 3:보합, 4:하락, 5:하락)
    @JsonProperty("prdy_ctrt") val changeRate: String,             // 전일 대비율
    @JsonProperty("acml_vol") val volume: String,                  // 누적 거래량
    @JsonProperty("acml_tr_pbmn") val tradeAmount: String,         // 누적 거래 대금
    
    // === 가격 정보 ===
    @JsonProperty("stck_oprc") val openPrice: String,             // 주식 시가
    @JsonProperty("stck_hgpr") val highPrice: String,             // 주식 최고가
    @JsonProperty("stck_lwpr") val lowPrice: String,              // 주식 최저가
    @JsonProperty("stck_mxpr") val upperLimit: String,            // 주식 상한가
    @JsonProperty("stck_llam") val lowerLimit: String,            // 주식 하한가
    
    // === 재무비율 ===
    val per: String,                                               // PER
    val pbr: String,                                               // PBR
    val eps: String,                                               // EPS
    val bps: String,                                               // BPS
    @JsonProperty("hts_avls") val marketCap: String,              // 시가총액
    
    // === 기술적 지표 ===
    @JsonProperty("w52_hgpr") val week52High: String,             // 52주 최고가
    @JsonProperty("w52_lwpr") val week52Low: String,              // 52주 최저가
    @JsonProperty("w52_hgpr_date") val week52HighDate: String,    // 52주 최고가 일자
    @JsonProperty("w52_lwpr_date") val week52LowDate: String,     // 52주 최저가 일자
    @JsonProperty("d250_hgpr") val day250High: String,            // 250일 최고가
    @JsonProperty("d250_lwpr") val day250Low: String,             // 250일 최저가
    @JsonProperty("stck_dryy_hgpr") val yearHigh: String,         // 연중 최고가
    @JsonProperty("stck_dryy_lwpr") val yearLow: String,          // 연중 최저가
    
    // === 시장 정보 ===
    @JsonProperty("hts_frgn_ehrt") val foreignOwnership: String,  // 외국인 소진율
    @JsonProperty("vol_tnrt") val volumeTurnover: String,         // 거래량 회전율
    @JsonProperty("rprs_mrkt_kor_name") val marketName: String,   // 대표 시장명
    @JsonProperty("bstp_kor_isnm") val sectorName: String,        // 업종명
    
    // === 기타 정보 ===
    @JsonProperty("lstn_stcn") val listedShares: String,          // 상장 주수
    @JsonProperty("stac_month") val settlementMonth: String,       // 결산월
    @JsonProperty("cpfn") val capital: String,                    // 자본금
    @JsonProperty("stck_fcam") val faceValue: String              // 액면가
)

/**
 * KIS Adapter 서버 상태 응답 DTO
 */
data class AdapterHealthResponse(
    val isHealthy: Boolean,
    val responseTimeMs: Long,
    val checkedAt: LocalDateTime,
    val serverInfo: Map<String, Any>? = null,
    val error: String? = null
)