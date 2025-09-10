package com.quantum.kis.application.dto

import com.quantum.kis.domain.KisEnvironment
import com.quantum.kis.domain.KisToken
import com.quantum.kis.domain.TokenStatus
import java.time.LocalDateTime
import java.time.temporal.ChronoUnit

/**
 * KIS 토큰 정보 애플리케이션 DTO
 * 애플리케이션 레이어에서 사용하는 토큰 정보 데이터 전송 객체
 */
data class KisTokenDto(
    val tokenId: Long,
    val accessToken: String,
    val expiresAt: LocalDateTime,
    val environment: KisEnvironment,
    val status: TokenStatus,
    val remainingTimeMinutes: Long
) {
    companion object {
        fun from(kisToken: KisToken): KisTokenDto {
            return KisTokenDto(
                tokenId = kisToken.id,
                accessToken = kisToken.accessToken,
                expiresAt = kisToken.expiresAt,
                environment = kisToken.environment,
                status = kisToken.status,
                remainingTimeMinutes = ChronoUnit.MINUTES.between(
                    LocalDateTime.now(),
                    kisToken.expiresAt
                ).coerceAtLeast(0)
            )
        }
    }
}