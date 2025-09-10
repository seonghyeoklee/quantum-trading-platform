package com.quantum.kis.application.service

import com.quantum.kis.domain.*
import com.quantum.kis.infrastructure.client.KisApiClient
import com.quantum.kis.infrastructure.client.KisApiException
import com.quantum.kis.infrastructure.repository.KisAccountRepository
import com.quantum.kis.infrastructure.repository.KisTokenRepository
import com.quantum.kis.application.dto.KisAccountRequest
import com.quantum.kis.application.dto.KisTokenDto
import kotlinx.coroutines.runBlocking
import org.slf4j.LoggerFactory
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.time.LocalDateTime
import java.util.concurrent.TimeUnit

/**
 * KIS 토큰 관리 서비스
 * 
 * 하이브리드 토큰 아키텍처의 핵심 서비스
 * 토큰 발급, 갱신, 자동 관리 담당
 */
@Service
@Transactional
class KisTokenService(
    private val kisAccountRepository: KisAccountRepository,
    private val kisTokenRepository: KisTokenRepository,
    private val kisApiClient: KisApiClient
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    /**
     * 새 토큰 발급
     * 
     * @param userId 사용자 ID
     * @param request 계정 요청 정보
     * @return 발급된 토큰 정보
     */
    suspend fun issueToken(userId: Long, request: KisAccountRequest): KisTokenDto {
        logger.info("Issuing new KIS token for user: $userId, environment: ${request.environment}")
        
        try {
            // 1. 계정 정보 저장 또는 업데이트
            val kisAccount = saveOrUpdateKisAccount(userId, request)
            
            // 2. 기존 활성 토큰 비활성화
            deactivateExistingTokens(userId, request.environment)
            
            // 3. KIS API로 토큰 발급 요청
            val tokenResponse = kisApiClient.getAccessToken(
                appKey = request.appKey,
                appSecret = request.appSecret,
                environment = request.environment
            )
            
            // 4. 토큰 DB 저장
            val kisToken = KisToken.create(
                userId = userId,
                kisAccountId = kisAccount.id,
                accessToken = tokenResponse.access_token,
                environment = request.environment,
                expiresAt = tokenResponse.getExpiresAt()
            )
            
            val savedToken = kisTokenRepository.save(kisToken)
            
            // 5. 계정에 토큰 발급 시간 기록
            kisAccount.markTokenIssued()
            kisAccountRepository.save(kisAccount)
            
            logger.info("Successfully issued KIS token for user: $userId")
            return KisTokenDto.from(savedToken)
            
        } catch (exception: Exception) {
            logger.error("Failed to issue KIS token for user: $userId", exception)
            throw KisTokenException("토큰 발급 실패: ${exception.message}", exception)
        }
    }
    
    /**
     * 토큰 갱신
     * 
     * @param userId 사용자 ID
     * @param environment KIS 환경
     * @return 갱신된 토큰 정보
     */
    suspend fun refreshToken(userId: Long, environment: KisEnvironment): KisTokenDto {
        logger.info("Refreshing KIS token for user: $userId, environment: ${environment.displayName}")
        
        try {
            // 1. 기존 계정 정보 조회
            val kisAccount = kisAccountRepository.findFirstByUserIdAndEnvironmentAndIsActiveTrueOrderByCreatedAtAsc(
                userId, environment
            ).orElseThrow { 
                KisAccountNotFoundException("활성화된 KIS 계정이 없습니다: userId=$userId, environment=$environment") 
            }
            
            // 2. 기존 토큰 갱신 시작 표시
            val existingToken = kisTokenRepository.findFirstByUserIdAndEnvironmentAndStatusOrderByCreatedAtDesc(
                userId, environment, TokenStatus.ACTIVE
            ).orElse(null)
            
            existingToken?.startRefresh()
            existingToken?.let { kisTokenRepository.save(it) }
            
            // 3. 새 토큰 발급
            val tokenResponse = kisApiClient.getAccessToken(
                appKey = kisAccount.appKey,
                appSecret = kisAccount.appSecret,
                environment = environment
            )
            
            if (existingToken != null) {
                // 4a. 기존 토큰 갱신
                existingToken.completeRefresh(
                    newAccessToken = tokenResponse.access_token,
                    newExpiresAt = tokenResponse.getExpiresAt()
                )
                val refreshedToken = kisTokenRepository.save(existingToken)
                
                logger.info("Successfully refreshed KIS token for user: $userId")
                return KisTokenDto.from(refreshedToken)
                
            } else {
                // 4b. 새 토큰 생성 (기존 토큰이 없는 경우)
                val newToken = KisToken.create(
                    userId = userId,
                    kisAccountId = kisAccount.id,
                    accessToken = tokenResponse.access_token,
                    environment = environment,
                    expiresAt = tokenResponse.getExpiresAt()
                )
                
                val savedToken = kisTokenRepository.save(newToken)
                
                logger.info("Created new KIS token for user: $userId (no existing token)")
                return KisTokenDto.from(savedToken)
            }
            
        } catch (exception: Exception) {
            logger.error("Failed to refresh KIS token for user: $userId", exception)
            
            // 갱신 실패 시 토큰 상태 업데이트
            kisTokenRepository.findFirstByUserIdAndEnvironmentAndStatusOrderByCreatedAtDesc(
                userId, environment, TokenStatus.REFRESHING
            ).ifPresent { token ->
                token.failRefresh()
                kisTokenRepository.save(token)
            }
            
            throw KisTokenException("토큰 갱신 실패: ${exception.message}", exception)
        }
    }
    
    /**
     * 계정 검증
     * 
     * @param userId 사용자 ID
     * @param request 계정 요청 정보
     * @return 검증 결과
     */
    suspend fun validateKisAccount(userId: Long, request: KisAccountRequest): Boolean {
        logger.info("Validating KIS account for user: $userId, environment: ${request.environment}")
        
        return try {
            val validationResponse = kisApiClient.validateAccount(
                appKey = request.appKey,
                appSecret = request.appSecret,
                environment = request.environment
            )
            
            if (validationResponse.isValid) {
                logger.info("KIS account validation successful for user: $userId")
            } else {
                logger.warn("KIS account validation failed for user: $userId - ${validationResponse.message}")
            }
            
            validationResponse.isValid
            
        } catch (exception: Exception) {
            logger.error("KIS account validation error for user: $userId", exception)
            false
        }
    }
    
    /**
     * 사용자별 환경별 활성 토큰 조회
     */
    @Transactional(readOnly = true)
    fun getActiveToken(userId: Long, environment: KisEnvironment): KisTokenDto? {
        return kisTokenRepository.findFirstByUserIdAndEnvironmentAndStatusOrderByCreatedAtDesc(
            userId, environment, TokenStatus.ACTIVE
        ).map { token ->
            // 토큰 사용 기록
            token.markUsed()
            kisTokenRepository.save(token)
            KisTokenDto.from(token)
        }.orElse(null)
    }
    
    /**
     * 자동 토큰 갱신 스케줄러 (1시간마다 실행)
     */
    @Scheduled(fixedRate = 1, timeUnit = TimeUnit.HOURS)
    fun scheduleTokenRefresh() {
        logger.info("Starting scheduled token refresh")
        
        val now = LocalDateTime.now()
        val tokensToRefresh = kisTokenRepository.findByStatusAndNextRefreshAtBeforeOrderByNextRefreshAtAsc(
            TokenStatus.ACTIVE, now
        )
        
        logger.info("Found ${tokensToRefresh.size} tokens to refresh")
        
        tokensToRefresh.forEach { token ->
            try {
                runBlocking {
                    refreshToken(token.userId, token.environment)
                }
                logger.info("Auto-refreshed token for user: ${token.userId}, environment: ${token.environment}")
                
            } catch (exception: Exception) {
                logger.error("Failed to auto-refresh token for user: ${token.userId}", exception)
            }
        }
        
        // 만료된 토큰 정리
        cleanupExpiredTokens()
    }
    
    /**
     * 만료된 토큰 정리 (배치 작업)
     */
    @Scheduled(fixedRate = 6, timeUnit = TimeUnit.HOURS)
    fun cleanupExpiredTokens() {
        logger.info("Starting expired token cleanup")
        
        val now = LocalDateTime.now()
        
        // 만료된 활성 토큰을 만료 상태로 변경
        val updatedCount = kisTokenRepository.bulkUpdateExpiredTokens(
            currentStatus = TokenStatus.ACTIVE,
            newStatus = TokenStatus.EXPIRED,
            expireTime = now,
            updateTime = now
        )
        
        logger.info("Updated $updatedCount expired tokens")
        
        // 오래된 만료 토큰 삭제 (30일 이후)
        val oldTokens = kisTokenRepository.findByStatusAndExpiresAtBefore(
            TokenStatus.EXPIRED, 
            now.minusDays(30)
        )
        
        if (oldTokens.isNotEmpty()) {
            kisTokenRepository.deleteAll(oldTokens)
            logger.info("Deleted ${oldTokens.size} old expired tokens")
        }
    }
    
    /**
     * 계정 저장 또는 업데이트
     */
    private suspend fun saveOrUpdateKisAccount(userId: Long, request: KisAccountRequest): KisAccount {
        val existingAccount = kisAccountRepository.findByUserIdAndEnvironmentAndAccountNumberAndIsActiveTrue(
            userId, request.environment, request.accountNumber
        )
        
        return if (existingAccount.isPresent) {
            // 기존 계정 업데이트
            val account = existingAccount.get()
            account.appKey = request.appKey
            account.appSecret = request.appSecret
            account.accountAlias = request.accountAlias
            account.markValidated()
            kisAccountRepository.save(account)
        } else {
            // 새 계정 생성
            val newAccount = KisAccount.create(
                userId = userId,
                appKey = request.appKey,
                appSecret = request.appSecret,
                accountNumber = request.accountNumber,
                environment = request.environment,
                accountAlias = request.accountAlias
            )
            kisAccountRepository.save(newAccount)
        }
    }
    
    /**
     * 기존 활성 토큰 비활성화
     */
    private fun deactivateExistingTokens(userId: Long, environment: KisEnvironment) {
        val activeTokens = kisTokenRepository.findByUserIdAndEnvironmentAndStatus(
            userId, environment, TokenStatus.ACTIVE
        )
        
        activeTokens.forEach { token ->
            token.revoke()
        }
        
        if (activeTokens.isNotEmpty()) {
            kisTokenRepository.saveAll(activeTokens)
            logger.debug("Deactivated ${activeTokens.size} existing tokens for user: $userId")
        }
    }
}


/**
 * KIS 토큰 예외 클래스
 */
class KisTokenException(
    message: String,
    cause: Throwable? = null
) : RuntimeException(message, cause)

/**
 * KIS 계정 찾기 실패 예외
 */
class KisAccountNotFoundException(
    message: String
) : RuntimeException(message)