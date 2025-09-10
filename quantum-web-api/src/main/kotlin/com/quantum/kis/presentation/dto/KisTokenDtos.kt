package com.quantum.kis.presentation.dto

import com.quantum.kis.domain.KisEnvironment
import com.quantum.kis.domain.KisToken
import com.quantum.kis.domain.TokenStatus
import io.swagger.v3.oas.annotations.media.Schema
import java.time.LocalDateTime

/**
 * KIS 계정 요청 DTO
 */
@Schema(description = "KIS 계정 정보 요청")
data class KisAccountRequest(
    @Schema(description = "앱 키", example = "your_app_key")
    val appKey: String,
    
    @Schema(description = "앱 시크릿", example = "your_app_secret") 
    val appSecret: String,
    
    @Schema(description = "계좌번호", example = "12345678")
    val accountNumber: String,
    
    @Schema(description = "KIS 환경", example = "LIVE")
    val environment: KisEnvironment,
    
    @Schema(description = "계정 별칭", example = "메인 투자 계좌")
    val accountAlias: String? = null
) {
    fun toApplication(): com.quantum.kis.application.dto.KisAccountRequest {
        return com.quantum.kis.application.dto.KisAccountRequest(
            appKey = appKey,
            appSecret = appSecret,
            accountNumber = accountNumber,
            environment = environment,
            accountAlias = accountAlias
        )
    }
}

/**
 * KIS 토큰 정보 DTO
 */
@Schema(description = "KIS 토큰 정보 응답")
data class KisTokenInfo(
    @Schema(description = "토큰 ID")
    val tokenId: Long,
    
    @Schema(description = "액세스 토큰")
    val accessToken: String,
    
    @Schema(description = "만료 시간")
    val expiresAt: LocalDateTime,
    
    @Schema(description = "KIS 환경")
    val environment: KisEnvironment,
    
    @Schema(description = "토큰 상태")
    val status: TokenStatus,
    
    @Schema(description = "남은 시간 (분)")
    val remainingTimeMinutes: Long
) {
    companion object {
        fun from(kisToken: KisToken): KisTokenInfo {
            return KisTokenInfo(
                tokenId = kisToken.id,
                accessToken = kisToken.accessToken,
                expiresAt = kisToken.expiresAt,
                environment = kisToken.environment,
                status = kisToken.status,
                remainingTimeMinutes = kisToken.getRemainingTime().toMinutes()
            )
        }
        
        fun from(kisTokenDto: com.quantum.kis.application.dto.KisTokenDto): KisTokenInfo {
            return KisTokenInfo(
                tokenId = kisTokenDto.tokenId,
                accessToken = kisTokenDto.accessToken,
                expiresAt = kisTokenDto.expiresAt,
                environment = kisTokenDto.environment,
                status = kisTokenDto.status,
                remainingTimeMinutes = kisTokenDto.remainingTimeMinutes
            )
        }
    }
}