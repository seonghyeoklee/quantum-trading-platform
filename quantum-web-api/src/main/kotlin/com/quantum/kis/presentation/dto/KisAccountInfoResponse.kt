package com.quantum.kis.presentation.dto

import io.swagger.v3.oas.annotations.media.Schema
import java.time.LocalDateTime

/**
 * KIS 계정 정보 응답 DTO
 */
@Schema(description = "KIS 계정 정보 응답")
data class KisAccountInfoResponse(
    @Schema(description = "앱 키 (암호화된 형태)", example = "encrypted_app_key")
    val appKey: String,
    
    @Schema(description = "앱 시크릿 (암호화된 형태)", example = "encrypted_app_secret")
    val appSecret: String,
    
    @Schema(description = "계좌번호", example = "12345678-01")
    val accountNumber: String,
    
    @Schema(description = "계정 별칭", example = "메인 투자 계좌")
    val accountAlias: String? = null,
    
    @Schema(description = "마지막 검증 시간")
    val lastValidatedAt: LocalDateTime? = null,
    
    @Schema(description = "마지막 토큰 발급 시간")
    val lastTokenIssuedAt: LocalDateTime? = null
)