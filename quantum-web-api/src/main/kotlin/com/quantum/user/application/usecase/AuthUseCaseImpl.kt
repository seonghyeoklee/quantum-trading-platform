package com.quantum.user.application.usecase

import com.quantum.user.application.port.incoming.*
import com.quantum.user.application.port.outgoing.PasswordEncodingPort
import com.quantum.user.application.port.outgoing.TokenManagementPort
import com.quantum.user.application.port.outgoing.UserRepository
import com.quantum.user.domain.UserDomainService
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

/**
 * 인증 관련 Use Case 구현체
 */
@Service
@Transactional
class AuthUseCaseImpl(
    private val userRepository: UserRepository,
    private val passwordEncodingPort: PasswordEncodingPort,
    private val tokenManagementPort: TokenManagementPort,
    private val userDomainService: UserDomainService
) : AuthUseCase {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    /**
     * 로그인
     */
    override fun login(command: LoginCommand): LoginResult {
        return try {
            logger.debug("Login attempt for email: ${command.email}")
            
            // 이메일 유효성 검사
            if (!userDomainService.validateEmail(command.email)) {
                return LoginResult(
                    success = false,
                    errorMessage = "올바르지 않은 이메일 형식입니다."
                )
            }
            
            // 사용자 조회
            val user = userRepository.findByEmail(command.email)
                .orElse(null)
            
            if (user == null) {
                logger.warn("Login failed: User not found with email ${command.email}")
                return LoginResult(
                    success = false,
                    errorMessage = "이메일 또는 비밀번호가 올바르지 않습니다."
                )
            }
            
            // 비밀번호 검증
            if (!passwordEncodingPort.matches(command.password, user.password)) {
                logger.warn("Login failed: Invalid password for email ${command.email}")
                return LoginResult(
                    success = false,
                    errorMessage = "이메일 또는 비밀번호가 올바르지 않습니다."
                )
            }
            
            // 로그인 처리 (도메인 로직)
            user.login()
            userRepository.save(user)
            
            // JWT 토큰 생성
            val accessToken = tokenManagementPort.generateToken(user)
            val expiresIn = tokenManagementPort.getTokenExpirationTime()
            
            logger.info("Login successful for email: ${command.email}")
            
            LoginResult(
                success = true,
                accessToken = accessToken,
                expiresIn = expiresIn,
                user = UserInfo.from(user)
            )
            
        } catch (exception: Exception) {
            logger.error("Login failed due to unexpected error", exception)
            LoginResult(
                success = false,
                errorMessage = "로그인 처리 중 오류가 발생했습니다."
            )
        }
    }
    
    /**
     * 사용자 정보 조회
     */
    @Transactional(readOnly = true)
    override fun getUserInfo(userId: Long): UserInfo {
        logger.debug("Getting user info for userId: $userId")
        
        val user = userRepository.findById(userId)
            .orElseThrow { IllegalArgumentException("사용자를 찾을 수 없습니다: $userId") }
        
        return UserInfo.from(user)
    }
    
    /**
     * 로그아웃 (단순히 성공 응답 반환 - 토큰 무효화는 클라이언트에서 처리)
     */
    override fun logout(userId: Long): LogoutResult {
        logger.info("Logout for userId: $userId")
        
        return LogoutResult(
            success = true,
            message = "로그아웃 완료"
        )
    }
}