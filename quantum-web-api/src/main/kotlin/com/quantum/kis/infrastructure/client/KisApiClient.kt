package com.quantum.kis.infrastructure.client

import com.quantum.kis.domain.KisEnvironment
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpHeaders
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.reactive.function.client.WebClient
import org.springframework.web.reactive.function.client.awaitBody
import org.springframework.web.reactive.function.client.awaitBodyOrNull
import java.time.LocalDateTime

/**
 * KIS API 클라이언트
 * 
 * 한국투자증권 Open API와 직접 통신하는 클라이언트
 * 하이브리드 토큰 아키텍처에서 토큰 발급/갱신을 담당
 */
@Component
class KisApiClient(
    private val webClient: WebClient,
    @Value("\${kis.api.live.base-url:https://openapi.koreainvestment.com:9443}") 
    private val liveBaseUrl: String,
    @Value("\${kis.api.sandbox.base-url:https://openapivts.koreainvestment.com:29443}") 
    private val sandboxBaseUrl: String
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    /**
     * KIS 액세스 토큰 발급
     */
    suspend fun getAccessToken(
        appKey: String,
        appSecret: String,
        environment: KisEnvironment
    ): KisTokenResponse {
        logger.info("Requesting KIS access token for environment: ${environment.displayName}")
        
        val baseUrl = getBaseUrl(environment)
        val requestBody = TokenRequest(
            grant_type = "client_credentials",
            appkey = appKey,
            appsecret = appSecret
        )
        
        return try {
            val response = webClient
                .post()
                .uri("$baseUrl/oauth2/tokenP")
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .bodyValue(requestBody)
                .retrieve()
                .awaitBody<KisTokenResponse>()
            
            logger.info("Successfully obtained KIS access token for ${environment.displayName}")
            response.copy(
                issuedAt = LocalDateTime.now(),
                environment = environment
            )
            
        } catch (exception: Exception) {
            logger.error("Failed to get KIS access token for ${environment.displayName}", exception)
            throw KisApiException("토큰 발급 실패: ${exception.message}", exception)
        }
    }
    
    /**
     * KIS 계정 정보 검증
     */
    suspend fun validateAccount(
        appKey: String,
        appSecret: String,
        environment: KisEnvironment
    ): AccountValidationResponse {
        logger.info("Validating KIS account for environment: ${environment.displayName}")
        
        return try {
            // 실제로는 토큰 발급을 시도해서 성공하면 유효한 계정으로 판단
            val tokenResponse = getAccessToken(appKey, appSecret, environment)
            
            AccountValidationResponse(
                isValid = true,
                message = "계정 정보가 유효합니다",
                environment = environment,
                validatedAt = LocalDateTime.now()
            )
            
        } catch (exception: Exception) {
            logger.error("KIS account validation failed for ${environment.displayName}", exception)
            AccountValidationResponse(
                isValid = false,
                message = exception.message ?: "계정 검증 실패",
                environment = environment,
                validatedAt = LocalDateTime.now(),
                error = exception.javaClass.simpleName
            )
        }
    }
    
    /**
     * KIS API 서버 상태 확인
     */
    suspend fun checkServerStatus(environment: KisEnvironment): ServerStatusResponse {
        logger.debug("Checking KIS server status for environment: ${environment.displayName}")
        
        val baseUrl = getBaseUrl(environment)
        
        return try {
            val startTime = System.currentTimeMillis()
            
            // 간단한 헬스체크 요청 (실제 KIS API에 따라 조정 필요)
            webClient
                .get()
                .uri("$baseUrl/")
                .retrieve()
                .awaitBodyOrNull<String>()
            
            val responseTime = System.currentTimeMillis() - startTime
            
            ServerStatusResponse(
                isAvailable = true,
                responseTimeMs = responseTime,
                environment = environment,
                checkedAt = LocalDateTime.now()
            )
            
        } catch (exception: Exception) {
            logger.warn("KIS server status check failed for ${environment.displayName}", exception)
            ServerStatusResponse(
                isAvailable = false,
                responseTimeMs = -1,
                environment = environment,
                checkedAt = LocalDateTime.now(),
                error = exception.message
            )
        }
    }
    
    /**
     * 환경별 기본 URL 반환
     */
    private fun getBaseUrl(environment: KisEnvironment): String {
        return when (environment) {
            KisEnvironment.LIVE -> liveBaseUrl
            KisEnvironment.SANDBOX -> sandboxBaseUrl
        }
    }
}

/**
 * 토큰 요청 DTO
 */
data class TokenRequest(
    val grant_type: String,
    val appkey: String,
    val appsecret: String
)

/**
 * KIS 토큰 응답 DTO
 */
data class KisTokenResponse(
    val access_token: String,
    val token_type: String = "Bearer",
    val expires_in: Int = 21600, // 6시간 (초 단위)
    val scope: String? = null,
    val issuedAt: LocalDateTime = LocalDateTime.now(),
    val environment: KisEnvironment = KisEnvironment.SANDBOX
) {
    /**
     * 만료 시간 계산
     */
    fun getExpiresAt(): LocalDateTime {
        return issuedAt.plusSeconds(expires_in.toLong())
    }
    
    /**
     * Authorization 헤더 값
     */
    fun getAuthorizationHeader(): String {
        return "$token_type $access_token"
    }
}

/**
 * 계정 검증 응답 DTO
 */
data class AccountValidationResponse(
    val isValid: Boolean,
    val message: String,
    val environment: KisEnvironment,
    val validatedAt: LocalDateTime,
    val error: String? = null
)

/**
 * 서버 상태 확인 응답 DTO
 */
data class ServerStatusResponse(
    val isAvailable: Boolean,
    val responseTimeMs: Long,
    val environment: KisEnvironment,
    val checkedAt: LocalDateTime,
    val error: String? = null
)

/**
 * KIS API 예외 클래스
 */
class KisApiException(
    message: String,
    cause: Throwable? = null
) : RuntimeException(message, cause)