package com.quantum.user.infrastructure.security

import com.quantum.config.JwtProperties
import com.quantum.user.application.port.outgoing.TokenManagementPort
import com.quantum.user.domain.User
import org.springframework.stereotype.Component

/**
 * 토큰 관리 어댑터
 */
@Component
class TokenManagementAdapter(
    private val jwtTokenProvider: JwtTokenProvider,
    private val jwtProperties: JwtProperties
) : TokenManagementPort {
    
    override fun generateToken(user: User): String {
        return jwtTokenProvider.generateToken(user)
    }
    
    override fun validateToken(token: String): Boolean {
        return jwtTokenProvider.validateToken(token)
    }
    
    override fun getUserIdFromToken(token: String): Long {
        return jwtTokenProvider.getUserIdFromToken(token)
    }
    
    override fun getTokenExpirationTime(): Long {
        return jwtProperties.expiration
    }
}