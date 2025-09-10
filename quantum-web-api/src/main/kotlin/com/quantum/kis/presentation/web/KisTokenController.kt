package com.quantum.kis.presentation.web

import com.quantum.kis.application.service.*
import com.quantum.kis.domain.KisEnvironment
import com.quantum.kis.presentation.dto.KisAccountRequest
import com.quantum.kis.presentation.dto.KisTokenInfo
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.Parameter
import io.swagger.v3.oas.annotations.media.Content
import io.swagger.v3.oas.annotations.media.Schema
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.security.SecurityRequirement
import io.swagger.v3.oas.annotations.tags.Tag
import org.slf4j.LoggerFactory
import org.springframework.http.ResponseEntity
import org.springframework.security.core.Authentication
import org.springframework.web.bind.annotation.*
import jakarta.validation.Valid
import java.time.LocalDateTime

/**
 * KIS 토큰 관리 컨트롤러
 * 
 * 하이브리드 토큰 아키텍처의 REST API
 * 토큰 발급, 갱신, 계정 검증 기능 제공
 */
@RestController
@RequestMapping("/api/v1/kis")
@Tag(name = "KIS Token Management", description = "KIS API 토큰 발급 및 관리 API")
class KisTokenController(
    private val kisTokenService: KisTokenService
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    /**
     * KIS 계정 검증
     */
    @PostMapping("/account/validate")
    @Operation(
        summary = "KIS 계정 검증", 
        description = "KIS 계정 정보의 유효성을 검증합니다. 실제 KIS API와 통신하여 계정 유효성을 확인합니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200", 
            description = "계정 검증 완료", 
            content = [Content(schema = Schema(implementation = KisAccountValidationResponse::class))]
        ),
        ApiResponse(
            responseCode = "400", 
            description = "잘못된 계정 정보 또는 검증 실패"
        ),
        ApiResponse(
            responseCode = "401", 
            description = "인증되지 않은 사용자"
        )
    )
    @SecurityRequirement(name = "bearerAuth")
    suspend fun validateAccount(
        @Parameter(description = "KIS 계정 검증 요청 정보", required = true)
        @RequestBody @Valid request: KisAccountValidationRequest,
        @Parameter(hidden = true) authentication: Authentication
    ): ResponseEntity<KisAccountValidationResponse> {
        return try {
            val userId = authentication.name.toLong()
            logger.info("Validating KIS account for user: $userId, environment: ${request.environment}")
            
            val accountRequest = com.quantum.kis.application.dto.KisAccountRequest(
                appKey = request.appKey,
                appSecret = request.appSecret,
                accountNumber = request.accountNumber,
                environment = request.environment,
                accountAlias = request.accountAlias
            )
            
            val isValid = kisTokenService.validateKisAccount(userId, accountRequest)
            
            val response = KisAccountValidationResponse(
                isValid = isValid,
                message = if (isValid) "계정 정보가 유효합니다" else "계정 정보가 올바르지 않습니다",
                environment = request.environment,
                validatedAt = LocalDateTime.now()
            )
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("Failed to validate KIS account", exception)
            
            val response = KisAccountValidationResponse(
                isValid = false,
                message = exception.message ?: "계정 검증 중 오류가 발생했습니다",
                environment = request.environment,
                validatedAt = LocalDateTime.now(),
                error = exception.javaClass.simpleName
            )
            
            ResponseEntity.badRequest().body(response)
        }
    }
    
    /**
     * KIS 토큰 발급
     */
    @PostMapping("/token")
    @Operation(
        summary = "KIS 토큰 발급", 
        description = "새로운 KIS 액세스 토큰을 발급합니다. 계정 정보를 저장하고 KIS API와 통신하여 토큰을 발급받습니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200", 
            description = "토큰 발급 성공", 
            content = [Content(schema = Schema(implementation = KisTokenResponse::class))]
        ),
        ApiResponse(
            responseCode = "400", 
            description = "잘못된 계정 정보"
        ),
        ApiResponse(
            responseCode = "401", 
            description = "인증되지 않은 사용자"
        ),
        ApiResponse(
            responseCode = "500", 
            description = "토큰 발급 실패"
        )
    )
    @SecurityRequirement(name = "bearerAuth")
    suspend fun issueToken(
        @Parameter(description = "KIS 토큰 발급 요청 정보", required = true)
        @RequestBody @Valid request: KisTokenIssueRequest,
        @Parameter(hidden = true) authentication: Authentication
    ): ResponseEntity<KisTokenResponse> {
        return try {
            val userId = authentication.name.toLong()
            logger.info("Issuing KIS token for user: $userId, environment: ${request.environment}")
            
            val accountRequest = com.quantum.kis.application.dto.KisAccountRequest(
                appKey = request.appKey,
                appSecret = request.appSecret,
                accountNumber = request.accountNumber,
                environment = request.environment,
                accountAlias = request.accountAlias
            )
            
            val tokenInfo = kisTokenService.issueToken(userId, accountRequest)
            
            val response = KisTokenResponse(
                token = tokenInfo.accessToken,
                expiresAt = tokenInfo.expiresAt,
                environment = tokenInfo.environment,
                tokenType = "Bearer",
                remainingMinutes = tokenInfo.remainingTimeMinutes,
                issuedAt = LocalDateTime.now()
            )
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("Failed to issue KIS token", exception)
            ResponseEntity.status(500).body(null)
        }
    }
    
    /**
     * KIS 토큰 갱신
     */
    @PostMapping("/token/refresh")
    @Operation(
        summary = "KIS 토큰 갱신", 
        description = "기존 KIS 토큰을 갱신합니다. 저장된 계정 정보를 사용하여 새로운 토큰을 발급받습니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200", 
            description = "토큰 갱신 성공", 
            content = [Content(schema = Schema(implementation = KisTokenResponse::class))]
        ),
        ApiResponse(
            responseCode = "400", 
            description = "저장된 계정 정보 없음"
        ),
        ApiResponse(
            responseCode = "401", 
            description = "인증되지 않은 사용자 또는 토큰 갱신 실패"
        )
    )
    @SecurityRequirement(name = "bearerAuth")
    suspend fun refreshToken(
        @Parameter(description = "KIS 토큰 갱신 요청 정보", required = true)
        @RequestBody @Valid request: KisTokenRefreshRequest,
        @Parameter(hidden = true) authentication: Authentication
    ): ResponseEntity<KisTokenResponse> {
        return try {
            val userId = authentication.name.toLong()
            logger.info("Refreshing KIS token for user: $userId, environment: ${request.environment}")
            
            val tokenInfo = kisTokenService.refreshToken(userId, request.environment)
            
            val response = KisTokenResponse(
                token = tokenInfo.accessToken,
                expiresAt = tokenInfo.expiresAt,
                environment = tokenInfo.environment,
                tokenType = "Bearer",
                remainingMinutes = tokenInfo.remainingTimeMinutes,
                issuedAt = LocalDateTime.now()
            )
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("Failed to refresh KIS token", exception)
            ResponseEntity.status(401).body(null)
        }
    }
    
    /**
     * 현재 활성 토큰 조회
     */
    @GetMapping("/token/current")
    @Operation(
        summary = "현재 토큰 조회", 
        description = "사용자의 현재 활성 토큰을 조회합니다. 토큰이 없으면 null을 반환합니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200", 
            description = "토큰 조회 성공", 
            content = [Content(schema = Schema(implementation = KisTokenResponse::class))]
        ),
        ApiResponse(
            responseCode = "401", 
            description = "인증되지 않은 사용자"
        ),
        ApiResponse(
            responseCode = "400", 
            description = "잘못된 요청"
        )
    )
    @SecurityRequirement(name = "bearerAuth")
    fun getCurrentToken(
        @Parameter(description = "KIS 환경 (LIVE 또는 SANDBOX)", required = true, example = "SANDBOX") 
        @RequestParam environment: KisEnvironment,
        @Parameter(hidden = true) authentication: Authentication
    ): ResponseEntity<KisTokenResponse?> {
        return try {
            val userId = authentication.name.toLong()
            val tokenInfo = kisTokenService.getActiveToken(userId, environment)
            
            val response = tokenInfo?.let { 
                KisTokenResponse(
                    token = it.accessToken,
                    expiresAt = it.expiresAt,
                    environment = it.environment,
                    tokenType = "Bearer",
                    remainingMinutes = it.remainingTimeMinutes,
                    issuedAt = LocalDateTime.now()
                )
            }
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("Failed to get current token", exception)
            ResponseEntity.badRequest().body(null)
        }
    }
    
    /**
     * 토큰 상태 확인
     */
    @GetMapping("/token/status")
    @Operation(
        summary = "토큰 상태 확인", 
        description = "토큰의 상태와 유효성을 확인합니다. 토큰 존재 여부, 유효성, 남은 시간 등을 포함한 상태 정보를 제공합니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200", 
            description = "토큰 상태 조회 성공", 
            content = [Content(schema = Schema(implementation = KisTokenStatusResponse::class))]
        ),
        ApiResponse(
            responseCode = "401", 
            description = "인증되지 않은 사용자"
        ),
        ApiResponse(
            responseCode = "400", 
            description = "잘못된 요청"
        )
    )
    @SecurityRequirement(name = "bearerAuth")
    fun getTokenStatus(
        @Parameter(description = "KIS 환경 (LIVE 또는 SANDBOX)", required = true, example = "SANDBOX") 
        @RequestParam environment: KisEnvironment,
        @Parameter(hidden = true) authentication: Authentication
    ): ResponseEntity<KisTokenStatusResponse> {
        return try {
            val userId = authentication.name.toLong()
            val tokenInfo = kisTokenService.getActiveToken(userId, environment)
            
            val response = if (tokenInfo != null) {
                KisTokenStatusResponse(
                    hasToken = true,
                    isValid = tokenInfo.remainingTimeMinutes > 0,
                    expiresAt = tokenInfo.expiresAt,
                    remainingMinutes = tokenInfo.remainingTimeMinutes,
                    status = tokenInfo.status.displayName,
                    environment = environment,
                    needsRefresh = tokenInfo.remainingTimeMinutes < 60 // 1시간 미만
                )
            } else {
                KisTokenStatusResponse(
                    hasToken = false,
                    isValid = false,
                    expiresAt = null,
                    remainingMinutes = 0,
                    status = "토큰 없음",
                    environment = environment,
                    needsRefresh = false
                )
            }
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("Failed to get token status", exception)
            ResponseEntity.badRequest().body(null)
        }
    }
}

/**
 * KIS 계정 검증 요청 DTO
 */
data class KisAccountValidationRequest(
    @field:Parameter(description = "KIS 앱 키", example = "your_app_key", required = true)
    val appKey: String,
    
    @field:Parameter(description = "KIS 앱 시크릿", example = "your_app_secret", required = true)
    val appSecret: String,
    
    @field:Parameter(description = "계좌번호 (8자리)", example = "12345678", required = true)
    val accountNumber: String,
    
    @field:Parameter(description = "KIS 환경", example = "SANDBOX", required = true)
    val environment: KisEnvironment,
    
    @field:Parameter(description = "계정 별칭 (선택사항)", example = "메인 투자 계좌")
    val accountAlias: String? = null
)

/**
 * KIS 계정 검증 응답 DTO
 */
data class KisAccountValidationResponse(
    @field:Parameter(description = "계정 유효성 여부", example = "true")
    val isValid: Boolean,
    
    @field:Parameter(description = "검증 결과 메시지", example = "계정 정보가 유효합니다")
    val message: String,
    
    @field:Parameter(description = "검증한 KIS 환경", example = "SANDBOX")
    val environment: KisEnvironment,
    
    @field:Parameter(description = "검증 완료 시각", example = "2024-01-01T12:00:00")
    val validatedAt: LocalDateTime,
    
    @field:Parameter(description = "오류 정보 (검증 실패 시)", example = "AUTHENTICATION_FAILED")
    val error: String? = null
)

/**
 * KIS 토큰 발급 요청 DTO
 */
data class KisTokenIssueRequest(
    val appKey: String,
    val appSecret: String,
    val accountNumber: String,
    val environment: KisEnvironment,
    val accountAlias: String? = null
)

/**
 * KIS 토큰 갱신 요청 DTO
 */
data class KisTokenRefreshRequest(
    val environment: KisEnvironment
)

/**
 * KIS 토큰 응답 DTO
 */
data class KisTokenResponse(
    val token: String,
    val expiresAt: LocalDateTime,
    val environment: KisEnvironment,
    val tokenType: String = "Bearer",
    val remainingMinutes: Long,
    val issuedAt: LocalDateTime,
    val error: String? = null
)

/**
 * KIS 토큰 상태 응답 DTO
 */
data class KisTokenStatusResponse(
    val hasToken: Boolean,
    val isValid: Boolean,
    val expiresAt: LocalDateTime?,
    val remainingMinutes: Long,
    val status: String,
    val environment: KisEnvironment,
    val needsRefresh: Boolean
)