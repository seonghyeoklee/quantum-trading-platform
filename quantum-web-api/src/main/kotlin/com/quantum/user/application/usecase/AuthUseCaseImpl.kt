package com.quantum.user.application.usecase

import com.quantum.user.application.port.incoming.*
import com.quantum.user.application.port.outgoing.PasswordEncodingPort
import com.quantum.user.application.port.outgoing.TokenManagementPort
import com.quantum.user.application.port.outgoing.UserRepository
import com.quantum.user.domain.UserDomainService
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import kotlinx.coroutines.runBlocking

/**
 * 인증 관련 Use Case 구현체
 */
@Service
@Transactional
class AuthUseCaseImpl(
    private val userRepository: UserRepository,
    private val passwordEncodingPort: PasswordEncodingPort,
    private val tokenManagementPort: TokenManagementPort,
    private val userDomainService: UserDomainService,
    private val kisTokenService: com.quantum.kis.application.service.KisTokenService,
    private val kisAccountRepository: com.quantum.kis.infrastructure.repository.KisAccountRepository
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
            
            // KIS 토큰 자동 발급 시도 (실패해도 로그인은 성공 처리)
            var kisTokenStatus: KisTokenStatus? = null
            try {
                kisTokenStatus = issueKisTokenIfAvailable(user.id)
            } catch (exception: Exception) {
                logger.warn("KIS token issuance failed for user ${user.id}", exception)
            }
            
            LoginResult(
                success = true,
                accessToken = accessToken,
                expiresIn = expiresIn,
                user = UserInfo.from(user),
                kisTokenStatus = kisTokenStatus
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
    
    /**
     * KIS 계정이 있는 사용자에게 KIS 토큰 자동 발급
     */
    private fun issueKisTokenIfAvailable(userId: Long): KisTokenStatus {
        // KIS 계정 존재 여부 확인
        val hasKisAccount = kisAccountRepository.existsByUserIdAndIsActiveTrue(userId)
        
        if (!hasKisAccount) {
            return KisTokenStatus(
                hasKisAccount = false,
                tokenIssued = false,
                environment = null
            )
        }
        
        // 우선순위: LIVE 환경 먼저 시도
        val environments = listOf(
            com.quantum.kis.domain.KisEnvironment.LIVE,
            com.quantum.kis.domain.KisEnvironment.SANDBOX
        )
        
        for (environment in environments) {
            val kisAccount = kisAccountRepository
                .findFirstByUserIdAndEnvironmentAndIsActiveTrueOrderByCreatedAtAsc(
                    userId, environment
                ).orElse(null)
                
            if (kisAccount != null) {
                try {
                    val request = com.quantum.kis.application.dto.KisAccountRequest(
                        appKey = kisAccount.appKey,
                        appSecret = kisAccount.appSecret,
                        accountNumber = kisAccount.accountNumber,
                        environment = environment,
                        accountAlias = kisAccount.accountAlias
                    )
                    
                    val kisTokenInfo = runBlocking {
                        kisTokenService.issueToken(userId, request)
                    }
                    logger.info("KIS token issued for user $userId: ${kisTokenInfo.tokenId}")
                    
                    return KisTokenStatus(
                        hasKisAccount = true,
                        tokenIssued = true,
                        environment = environment.displayName
                    )
                    
                } catch (exception: Exception) {
                    logger.warn("Failed to issue KIS token for user $userId in $environment", exception)
                    // 다음 환경으로 계속 시도
                    continue
                }
            }
        }
        
        // 모든 환경에서 토큰 발급 실패
        return KisTokenStatus(
            hasKisAccount = true,
            tokenIssued = false,
            environment = null
        )
    }
}