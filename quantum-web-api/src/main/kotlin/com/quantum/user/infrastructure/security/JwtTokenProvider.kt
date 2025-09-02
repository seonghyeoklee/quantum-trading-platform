package com.quantum.user.infrastructure.security

import com.quantum.config.JwtProperties
import com.quantum.user.domain.User
import io.jsonwebtoken.*
import io.jsonwebtoken.security.Keys
import jakarta.annotation.PostConstruct
import org.springframework.stereotype.Component
import java.security.Key
import java.util.*

/**
 * JWT 토큰 생성 및 검증을 담당하는 유틸리티
 */
@Component
class JwtTokenProvider(
    private val jwtProperties: JwtProperties
) {
    
    private lateinit var key: Key
    
    @PostConstruct
    fun init() {
        key = Keys.hmacShaKeyFor(jwtProperties.secret.toByteArray())
    }
    
    /**
     * 사용자 정보로 JWT 토큰 생성
     */
    fun generateToken(user: User): String {
        val now = Date()
        val expiryDate = Date(now.time + jwtProperties.expiration * 1000)
        
        return Jwts.builder()
            .setSubject(user.id.toString())
            .claim("email", user.email)
            .claim("name", user.name)
            .claim("roles", user.roles.map { it.name })
            .setIssuedAt(now)
            .setExpiration(expiryDate)
            .signWith(key, SignatureAlgorithm.HS512)
            .compact()
    }
    
    /**
     * 토큰에서 사용자 ID 추출
     */
    fun getUserIdFromToken(token: String): Long {
        val claims = getClaimsFromToken(token)
        return claims.subject.toLong()
    }
    
    /**
     * 토큰에서 이메일 추출
     */
    fun getEmailFromToken(token: String): String {
        val claims = getClaimsFromToken(token)
        return claims.get("email", String::class.java)
    }
    
    /**
     * 토큰 유효성 검사
     */
    fun validateToken(token: String): Boolean {
        return try {
            getClaimsFromToken(token)
            true
        } catch (ex: JwtException) {
            false
        } catch (ex: IllegalArgumentException) {
            false
        }
    }
    
    /**
     * 토큰 만료 시간 확인
     */
    fun getExpirationDateFromToken(token: String): Date {
        val claims = getClaimsFromToken(token)
        return claims.expiration
    }
    
    /**
     * 토큰이 만료되었는지 확인
     */
    fun isTokenExpired(token: String): Boolean {
        val expiration = getExpirationDateFromToken(token)
        return expiration.before(Date())
    }
    
    /**
     * 토큰에서 Claims 추출
     */
    private fun getClaimsFromToken(token: String): Claims {
        return Jwts.parser()
            .setSigningKey(key)
            .parseClaimsJws(token)
            .body
    }
    
    /**
     * Bearer 토큰에서 실제 토큰 부분 추출
     */
    fun resolveToken(bearerToken: String?): String? {
        return if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            bearerToken.substring(7)
        } else null
    }
}