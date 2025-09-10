package com.quantum.kis.application.port.outgoing

import com.quantum.kis.domain.KisEnvironment

/**
 * KIS API 클라이언트 관련 출력 포트 (헥사고날 아키텍처)
 */
interface KisApiPort {
    
    /**
     * 토큰 발급 요청
     */
    suspend fun issueToken(
        appKey: String,
        appSecret: String,
        environment: KisEnvironment
    ): String?
    
    /**
     * 토큰 폐기 요청
     */
    suspend fun revokeToken(
        accessToken: String,
        appKey: String,
        appSecret: String,
        environment: KisEnvironment
    ): Boolean
}