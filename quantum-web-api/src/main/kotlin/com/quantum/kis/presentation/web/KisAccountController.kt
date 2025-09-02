package com.quantum.kis.presentation.web

import com.quantum.kis.application.service.KisAccountService
import com.quantum.kis.application.service.KisTokenService
import com.quantum.kis.application.service.KisTokenInfo
import com.quantum.kis.domain.KisEnvironment
import com.quantum.kis.presentation.dto.KisAccountInfoResponse
import com.quantum.user.infrastructure.security.JwtTokenProvider
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.Parameter
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.responses.ApiResponse as SwaggerApiResponse
import io.swagger.v3.oas.annotations.tags.Tag
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

/**
 * KIS 계정 관리 컨트롤러
 * 
 * MVP 1.0 Complete Login-KIS Token Integration에서 요구하는 핵심 API 구현:
 * - GET /api/v1/kis-accounts/me: 사용자 KIS 계정 정보 조회
 * - POST /api/v1/kis-accounts/me/token: 저장된 계정으로 토큰 발급
 */
@RestController
@RequestMapping("/api/v1/kis-accounts")
@Tag(name = "KIS Account Management", description = "사용자별 KIS 계정 관리 API")
class KisAccountController(
    private val kisAccountService: KisAccountService,
    private val kisTokenService: KisTokenService,
    private val jwtTokenProvider: JwtTokenProvider
) {
    
    private val logger = LoggerFactory.getLogger(KisAccountController::class.java)
    
    /**
     * HTTP 요청에서 JWT 토큰을 추출하여 사용자 ID를 가져오는 유틸리티 메서드
     */
    private fun getUserIdFromRequest(request: jakarta.servlet.http.HttpServletRequest): Long {
        val bearerToken = request.getHeader("Authorization")
        val jwt = jwtTokenProvider.resolveToken(bearerToken)
            ?: throw IllegalArgumentException("인증 토큰이 필요합니다. Authorization 헤더에 Bearer 토큰을 포함해주세요.")
        
        return jwtTokenProvider.getUserIdFromToken(jwt)
    }
    
    /**
     * 사용자 KIS 계정 정보 조회
     * 
     * MVP 문서 요구사항: GET /api/v1/kis-accounts/me
     * Response: { "live": {...}, "sandbox": {...} }
     */
    @GetMapping("/me")
    @Operation(
        summary = "사용자 KIS 계정 정보 조회",
        description = "현재 인증된 사용자의 KIS 계정 정보를 조회합니다. LIVE와 SANDBOX 환경별로 반환됩니다."
    )
    @ApiResponses(
        SwaggerApiResponse(responseCode = "200", description = "조회 성공"),
        SwaggerApiResponse(responseCode = "401", description = "인증 실패")
    )
    fun getMyKisAccounts(
        request: jakarta.servlet.http.HttpServletRequest
    ): ResponseEntity<Map<String, KisAccountInfoResponse?>> {
        return try {
            val userId = getUserIdFromRequest(request)
            logger.info("KIS 계정 정보 조회 요청 - 사용자 ID: {}", userId)
            
            val accountsInfo = kisAccountService.getUserKisAccounts(userId)
            
            logger.info("KIS 계정 정보 조회 완료 - 사용자 ID: {}, LIVE 계정: {}, SANDBOX 계정: {}", 
                userId, 
                if (accountsInfo["live"] != null) "있음" else "없음",
                if (accountsInfo["sandbox"] != null) "있음" else "없음"
            )
            
            ResponseEntity.ok(accountsInfo)
            
        } catch (exception: Exception) {
            logger.error("KIS 계정 정보 조회 실패", exception)
            ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(null)
        }
    }
    
    /**
     * 저장된 KIS 계정으로 토큰 발급
     * 
     * MVP 문서 요구사항: POST /api/v1/kis-accounts/me/token
     * Request: { "environment": "LIVE" | "SANDBOX" }
     * Response: { "success": true, "token": "...", "expiresIn": 21600, "environment": "LIVE" }
     */
    @PostMapping("/me/token")
    @Operation(
        summary = "저장된 KIS 계정으로 토큰 발급",
        description = "사용자의 저장된 KIS 계정 정보를 사용하여 액세스 토큰을 발급합니다."
    )
    @ApiResponses(
        SwaggerApiResponse(responseCode = "200", description = "토큰 발급 성공"),
        SwaggerApiResponse(responseCode = "400", description = "계정 정보 없음 또는 잘못된 요청"),
        SwaggerApiResponse(responseCode = "401", description = "인증 실패"),
        SwaggerApiResponse(responseCode = "500", description = "토큰 발급 실패")
    )
    suspend fun issueTokenFromStoredAccount(
        @RequestBody request: KisTokenIssueFromStoredAccountRequest,
        httpRequest: jakarta.servlet.http.HttpServletRequest
    ): ResponseEntity<KisTokenIssueResponse> {
        return try {
            val userId = getUserIdFromRequest(httpRequest)
            logger.info("저장된 계정으로 KIS 토큰 발급 요청 - 사용자 ID: {}, 환경: {}", userId, request.environment)
            
            // 사용자의 해당 환경 계정 확인
            kisAccountService.getUserKisAccount(userId, request.environment)
                ?: return ResponseEntity.badRequest()
                    .body(null)
            
            // 기존 토큰 갱신 로직 활용
            val tokenInfo = kisTokenService.refreshToken(userId, request.environment)
            
            val response = KisTokenIssueResponse(
                success = true,
                token = tokenInfo.accessToken,
                expiresIn = 21600, // 6시간 (초)
                environment = request.environment.name
            )
            
            logger.info("저장된 계정으로 KIS 토큰 발급 성공 - 사용자 ID: {}, 환경: {}, 토큰 만료: {}", 
                userId, request.environment, tokenInfo.expiresAt)
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("저장된 계정으로 KIS 토큰 발급 실패", exception)
            
            val errorMessage = when {
                exception.message?.contains("No active KIS account found") == true -> 
                    "해당 환경(${request.environment})의 활성 KIS 계정이 없습니다."
                exception.message?.contains("KIS API") == true -> 
                    "KIS API 호출 중 오류가 발생했습니다: ${exception.message}"
                else -> "토큰 발급 중 오류가 발생했습니다: ${exception.message}"
            }
            
            ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(null)
        }
    }
    
    /**
     * KIS 계정 설정 (신규 등록 또는 업데이트)
     * 
     * MVP 문서 요구사항: POST /api/v1/kis-accounts/setup
     * Request: { "appKey": "...", "appSecret": "...", "accountNumber": "...", "environment": "LIVE", "accountAlias": "..." }
     * Response: { "success": true, "message": "KIS 계정이 설정되었습니다." }
     */
    @PostMapping("/setup")
    @Operation(
        summary = "KIS 계정 설정",
        description = "사용자의 KIS 계정 정보를 신규 등록하거나 업데이트합니다."
    )
    @ApiResponses(
        SwaggerApiResponse(responseCode = "200", description = "계정 설정 성공"),
        SwaggerApiResponse(responseCode = "400", description = "잘못된 계정 정보"),
        SwaggerApiResponse(responseCode = "401", description = "인증 실패"),
        SwaggerApiResponse(responseCode = "500", description = "서버 오류")
    )
    fun setupKisAccount(
        @RequestBody request: KisAccountSetupRequest,
        httpRequest: jakarta.servlet.http.HttpServletRequest
    ): ResponseEntity<KisAccountSetupResponse> {
        return try {
            val userId = getUserIdFromRequest(httpRequest)
            logger.info("KIS 계정 설정 요청 - 사용자 ID: {}, 환경: {}", userId, request.environment)
            
            // 계정 정보 저장
            val savedAccount = kisAccountService.saveOrUpdateKisAccount(
                userId = userId,
                appKey = request.appKey,
                appSecret = request.appSecret,
                accountNumber = request.accountNumber,
                environment = request.environment,
                accountAlias = request.accountAlias
            )
            
            val response = KisAccountSetupResponse(
                success = true,
                message = "KIS 계정이 성공적으로 설정되었습니다.",
                accountId = savedAccount.id,
                environment = request.environment.name
            )
            
            logger.info("KIS 계정 설정 성공 - 사용자 ID: {}, 계정 ID: {}, 환경: {}", 
                userId, savedAccount.id, request.environment)
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("KIS 계정 설정 실패", exception)
            
            val errorMessage = when {
                exception.message?.contains("duplicate") == true -> 
                    "이미 등록된 계정 정보입니다."
                exception.message?.contains("validation") == true -> 
                    "계정 정보가 올바르지 않습니다: ${exception.message}"
                else -> "계정 설정 중 오류가 발생했습니다: ${exception.message}"
            }
            
            ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(null)
        }
    }

    /**
     * 특정 환경의 KIS 계정 존재 여부 확인
     */
    @GetMapping("/me/exists")
    @Operation(
        summary = "KIS 계정 존재 여부 확인",
        description = "사용자가 특정 환경의 KIS 계정을 가지고 있는지 확인합니다."
    )
    fun hasKisAccount(
        @Parameter(description = "KIS 환경") @RequestParam environment: KisEnvironment,
        request: jakarta.servlet.http.HttpServletRequest
    ): ResponseEntity<KisAccountExistsResponse> {
        return try {
            val userId = getUserIdFromRequest(request)
            val hasAccount = kisAccountService.hasKisAccount(userId, environment)
            
            val response = KisAccountExistsResponse(
                hasAccount = hasAccount,
                environment = environment.name
            )
            
            ResponseEntity.ok(response)
            
        } catch (exception: Exception) {
            logger.error("KIS 계정 존재 여부 확인 실패", exception)
            ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(null)
        }
    }
}

/**
 * KIS 토큰 발급 응답 DTO
 */
data class KisTokenIssueResponse(
    @field:Parameter(description = "발급 성공 여부")
    val success: Boolean,
    
    @field:Parameter(description = "액세스 토큰")
    val token: String,
    
    @field:Parameter(description = "만료 시간 (초)", example = "21600")
    val expiresIn: Int,
    
    @field:Parameter(description = "환경", example = "LIVE")
    val environment: String
)

/**
 * 저장된 KIS 계정으로 토큰 발급 요청 DTO
 */
data class KisTokenIssueFromStoredAccountRequest(
    @field:Parameter(description = "KIS 환경", example = "SANDBOX")
    val environment: KisEnvironment
)

/**
 * KIS 계정 설정 요청 DTO
 */
data class KisAccountSetupRequest(
    @field:Parameter(description = "KIS 앱 키", example = "your_app_key")
    val appKey: String,
    
    @field:Parameter(description = "KIS 앱 시크릿", example = "your_app_secret")
    val appSecret: String,
    
    @field:Parameter(description = "계좌번호", example = "12345678-01")
    val accountNumber: String,
    
    @field:Parameter(description = "KIS 환경", example = "SANDBOX")
    val environment: KisEnvironment,
    
    @field:Parameter(description = "계정 별칭 (선택사항)", example = "메인 투자 계좌")
    val accountAlias: String? = null
)

/**
 * KIS 계정 설정 응답 DTO
 */
data class KisAccountSetupResponse(
    @field:Parameter(description = "설정 성공 여부")
    val success: Boolean,
    
    @field:Parameter(description = "응답 메시지")
    val message: String,
    
    @field:Parameter(description = "생성된 계정 ID")
    val accountId: Long,
    
    @field:Parameter(description = "환경", example = "SANDBOX")
    val environment: String
)

/**
 * KIS 계정 존재 여부 응답 DTO
 */
data class KisAccountExistsResponse(
    @field:Parameter(description = "계정 존재 여부")
    val hasAccount: Boolean,
    
    @field:Parameter(description = "환경", example = "SANDBOX")
    val environment: String
)