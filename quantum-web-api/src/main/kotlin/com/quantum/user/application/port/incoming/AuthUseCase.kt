package com.quantum.user.application.port.incoming

import com.quantum.user.domain.User

/**
 * 인증 관련 Use Case 인터페이스 (헥사고날 아키텍처의 인커밍 포트)
 */
interface AuthUseCase {
    
    /**
     * 로그인
     */
    fun login(command: LoginCommand): LoginResult
    
    /**
     * 사용자 정보 조회
     */
    fun getUserInfo(userId: Long): UserInfo
    
    /**
     * 로그아웃 (토큰 무효화는 클라이언트에서 처리)
     */
    fun logout(userId: Long): LogoutResult
}

/**
 * 로그인 명령
 */
data class LoginCommand(
    val email: String,
    val password: String
)

/**
 * 로그인 결과
 */
data class LoginResult(
    val success: Boolean,
    val accessToken: String? = null,
    val expiresIn: Long? = null,
    val user: UserInfo? = null,
    val errorMessage: String? = null,
    val kisTokenStatus: KisTokenStatus? = null
)

/**
 * 사용자 정보
 */
data class UserInfo(
    val id: Long,
    val email: String,
    val name: String,
    val roles: Set<String>,
    val lastLoginAt: String? = null
) {
    companion object {
        fun from(user: User): UserInfo {
            return UserInfo(
                id = user.id,
                email = user.email,
                name = user.name,
                roles = user.roles.map { it.name }.toSet(),
                lastLoginAt = user.lastLoginAt?.toString()
            )
        }
    }
}

/**
 * 로그아웃 결과
 */
data class LogoutResult(
    val success: Boolean,
    val message: String
)

/**
 * KIS 토큰 상태
 */
data class KisTokenStatus(
    val hasKisAccount: Boolean,
    val tokenIssued: Boolean,
    val environment: String?
)