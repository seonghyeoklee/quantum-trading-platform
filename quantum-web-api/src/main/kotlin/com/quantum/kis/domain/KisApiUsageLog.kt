package com.quantum.kis.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import java.time.LocalDateTime

/**
 * KIS API 호출 이력 및 유량 관리 로그
 * 
 * Rate Limiting을 위한 API 호출 추적 및 분석 데이터
 */
@Entity
@Table(
    name = "kis_api_usage_log",
    indexes = [
        Index(name = "idx_kis_api_usage_setting_time", columnList = "kis_setting_id, called_at"),
        Index(name = "idx_kis_api_usage_environment_time", columnList = "environment, called_at"),
        Index(name = "idx_kis_api_usage_rate_limited", columnList = "is_rate_limited, called_at")
    ]
)
class KisApiUsageLog(
    /**
     * KIS 설정 ID (Foreign Key)
     */
    @Column(name = "kis_setting_id", nullable = false)
    var kisSettingId: Long = 0L,
    
    /**
     * API 엔드포인트
     */
    @Column(name = "api_endpoint", nullable = false, length = 255)
    var apiEndpoint: String = "",
    
    /**
     * HTTP 메소드
     */
    @Column(name = "http_method", nullable = false, length = 10)
    var httpMethod: String = "",
    
    /**
     * 호출 시간
     */
    @Column(name = "called_at", nullable = false)
    var calledAt: LocalDateTime = LocalDateTime.now(),
    
    /**
     * HTTP 응답 상태 코드
     */
    @Column(name = "response_status")
    var responseStatus: Int? = null,
    
    /**
     * 응답 시간 (밀리초)
     */
    @Column(name = "response_time_ms")
    var responseTimeMs: Int? = null,
    
    /**
     * API 환경 (LIVE/SANDBOX)
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    var environment: KisEnvironment = KisEnvironment.SANDBOX,
    
    /**
     * 남은 호출 수 (응답 헤더 기반)
     */
    @Column(name = "rate_limit_remaining")
    var rateLimitRemaining: Int? = null,
    
    /**
     * 제한 리셋 시간
     */
    @Column(name = "rate_limit_reset_at")
    var rateLimitResetAt: LocalDateTime? = null,
    
    /**
     * 유량 제한으로 인한 거부 여부
     */
    @Column(name = "is_rate_limited", nullable = false)
    var isRateLimited: Boolean = false,
    
    /**
     * 에러 메시지
     */
    @Column(name = "error_message", columnDefinition = "TEXT")
    var errorMessage: String? = null

) : BaseEntity() {
    
    /**
     * JPA를 위한 기본 생성자
     */
    protected constructor() : this(
        kisSettingId = 0L,
        apiEndpoint = "",
        httpMethod = "",
        calledAt = LocalDateTime.now()
    )
    
    /**
     * API 호출 성공 여부 확인
     */
    fun isSuccessful(): Boolean {
        return responseStatus != null && responseStatus!! in 200..299
    }
    
    /**
     * 서버 에러 여부 확인
     */
    fun isServerError(): Boolean {
        return responseStatus != null && responseStatus!! >= 500
    }
    
    /**
     * 클라이언트 에러 여부 확인
     */
    fun isClientError(): Boolean {
        return responseStatus != null && responseStatus!! in 400..499
    }
    
    /**
     * 응답 시간이 느린지 확인 (1초 이상)
     */
    fun isSlowResponse(): Boolean {
        return responseTimeMs != null && responseTimeMs!! > 1000
    }
    
    /**
     * 로그 요약 정보 생성
     */
    fun getSummary(): String {
        val status = when {
            isRateLimited -> "RATE_LIMITED"
            isSuccessful() -> "SUCCESS"
            isClientError() -> "CLIENT_ERROR"
            isServerError() -> "SERVER_ERROR"
            else -> "UNKNOWN"
        }
        
        return "$httpMethod $apiEndpoint -> $status (${responseTimeMs}ms)"
    }
    
    companion object {
        /**
         * 성공한 API 호출 로그 생성
         */
        fun createSuccessLog(
            kisSettingId: Long,
            environment: KisEnvironment,
            apiEndpoint: String,
            httpMethod: String,
            responseStatus: Int,
            responseTimeMs: Int,
            rateLimitRemaining: Int? = null
        ): KisApiUsageLog {
            return KisApiUsageLog(
                kisSettingId = kisSettingId,
                apiEndpoint = apiEndpoint,
                httpMethod = httpMethod,
                environment = environment,
                responseStatus = responseStatus,
                responseTimeMs = responseTimeMs,
                rateLimitRemaining = rateLimitRemaining,
                isRateLimited = false
            )
        }
        
        /**
         * 유량 제한으로 거부된 API 호출 로그 생성
         */
        fun createRateLimitedLog(
            kisSettingId: Long,
            environment: KisEnvironment,
            apiEndpoint: String,
            httpMethod: String,
            errorMessage: String
        ): KisApiUsageLog {
            return KisApiUsageLog(
                kisSettingId = kisSettingId,
                apiEndpoint = apiEndpoint,
                httpMethod = httpMethod,
                environment = environment,
                responseStatus = 429, // Too Many Requests
                isRateLimited = true,
                errorMessage = errorMessage
            )
        }
    }
}