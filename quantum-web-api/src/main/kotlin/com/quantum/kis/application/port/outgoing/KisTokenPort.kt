package com.quantum.kis.application.port.outgoing

import com.quantum.kis.domain.KisToken
import com.quantum.kis.domain.KisEnvironment
import com.quantum.kis.domain.TokenStatus
import java.time.LocalDateTime
import java.util.*

/**
 * KIS 토큰 관련 출력 포트 (헥사고날 아키텍처)
 */
interface KisTokenPort {
    
    /**
     * 사용자 ID와 환경으로 활성 토큰 조회
     */
    fun findByUserIdAndEnvironmentAndStatus(
        userId: Long, 
        environment: KisEnvironment, 
        status: TokenStatus
    ): List<KisToken>
    
    /**
     * KIS 토큰 저장
     */
    fun save(kisToken: KisToken): KisToken
    
    /**
     * 만료된 토큰 일괄 업데이트
     */
    fun bulkUpdateExpiredTokens(
        fromStatus: TokenStatus,
        toStatus: TokenStatus,
        beforeTime: LocalDateTime,
        currentTime: LocalDateTime
    ): Int
    
    /**
     * 토큰 일괄 삭제
     */
    fun deleteAll(tokens: Iterable<KisToken>)
}