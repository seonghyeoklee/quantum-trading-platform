package com.quantum.user.application.port.outgoing

import com.quantum.user.domain.User

/**
 * 토큰 관리 포트
 */
interface TokenManagementPort {
    
    /**
     * JWT 토큰 생성
     */
    fun generateToken(user: User): String
    
    /**
     * 토큰 유효성 검증
     */
    fun validateToken(token: String): Boolean
    
    /**
     * 토큰에서 사용자 ID 추출
     */
    fun getUserIdFromToken(token: String): Long
    
    /**
     * 토큰 만료 시간(초) 조회
     */
    fun getTokenExpirationTime(): Long
}