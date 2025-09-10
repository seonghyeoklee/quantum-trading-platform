package com.quantum.kis.application.dto

import com.quantum.kis.domain.KisEnvironment
import java.time.LocalDateTime

/**
 * KIS 계정 요청 애플리케이션 DTO
 * 애플리케이션 레이어에서 사용하는 계정 정보 데이터 전송 객체
 */
data class KisAccountRequest(
    val appKey: String,
    val appSecret: String,
    val accountNumber: String,
    val environment: KisEnvironment,
    val accountAlias: String? = null
)

/**
 * KIS 계정 정보 응답 애플리케이션 DTO
 * 애플리케이션 레이어에서 사용하는 계정 정보 응답 데이터 전송 객체
 */
data class KisAccountInfoDto(
    val appKey: String,
    val appSecret: String,
    val accountNumber: String,
    val accountAlias: String?,
    val lastValidatedAt: LocalDateTime?,
    val lastTokenIssuedAt: LocalDateTime?
)