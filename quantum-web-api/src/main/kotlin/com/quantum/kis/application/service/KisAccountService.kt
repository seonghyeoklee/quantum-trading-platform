package com.quantum.kis.application.service

import com.quantum.kis.application.dto.KisAccountInfoDto
import com.quantum.kis.application.port.outgoing.KisAccountPort
import com.quantum.kis.domain.KisAccount
import com.quantum.kis.domain.KisEnvironment
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

/**
 * 사용자별 KIS 계정 관리 서비스
 */
@Service
@Transactional
class KisAccountService(
    private val kisAccountPort: KisAccountPort
) {
    
    /**
     * 사용자의 KIS 계정 정보 조회
     */
    @Transactional(readOnly = true)
    fun getUserKisAccounts(userId: Long): Map<String, KisAccountInfoDto?> {
        val accounts = kisAccountPort.findByUserIdAndIsActiveTrue(userId)
        
        val result = mutableMapOf<String, KisAccountInfoDto?>()
        
        // LIVE 환경 계정 찾기
        val liveAccount = accounts.find { it.environment == KisEnvironment.LIVE }
        result["live"] = liveAccount?.let { account ->
            KisAccountInfoDto(
                appKey = account.appKey,
                appSecret = account.appSecret, // 암호화된 상태로 반환
                accountNumber = account.accountNumber,
                accountAlias = account.accountAlias,
                lastValidatedAt = account.lastValidatedAt,
                lastTokenIssuedAt = account.lastTokenIssuedAt
            )
        }
        
        // SANDBOX 환경 계정 찾기
        val sandboxAccount = accounts.find { it.environment == KisEnvironment.SANDBOX }
        result["sandbox"] = sandboxAccount?.let { account ->
            KisAccountInfoDto(
                appKey = account.appKey,
                appSecret = account.appSecret, // 암호화된 상태로 반환
                accountNumber = account.accountNumber,
                accountAlias = account.accountAlias,
                lastValidatedAt = account.lastValidatedAt,
                lastTokenIssuedAt = account.lastTokenIssuedAt
            )
        }
        
        return result
    }
    
    /**
     * 특정 환경의 사용자 KIS 계정 조회 (첫 번째 계정)
     */
    @Transactional(readOnly = true)
    fun getUserKisAccount(userId: Long, environment: KisEnvironment): KisAccount? {
        return kisAccountPort.findFirstByUserIdAndEnvironmentAndIsActiveTrueOrderByCreatedAtAsc(
            userId, environment
        ).orElse(null)
    }
    
    /**
     * 사용자가 KIS 계정을 가지고 있는지 확인
     */
    @Transactional(readOnly = true)
    fun hasKisAccount(userId: Long): Boolean {
        return kisAccountPort.existsByUserIdAndIsActiveTrue(userId)
    }
    
    /**
     * 특정 환경의 KIS 계정 존재 여부 확인
     */
    @Transactional(readOnly = true)
    fun hasKisAccount(userId: Long, environment: KisEnvironment): Boolean {
        return kisAccountPort.findFirstByUserIdAndEnvironmentAndIsActiveTrueOrderByCreatedAtAsc(
            userId, environment
        ).isPresent
    }
    
    /**
     * KIS 계정 저장 또는 업데이트
     */
    fun saveOrUpdateKisAccount(
        userId: Long,
        appKey: String,
        appSecret: String,
        accountNumber: String,
        environment: KisEnvironment,
        accountAlias: String? = null
    ): KisAccount {
        // 기존 계정이 있는지 확인
        val existingAccount = kisAccountPort.findFirstByUserIdAndEnvironmentAndIsActiveTrueOrderByCreatedAtAsc(
            userId, environment
        ).orElse(null)
        
        return if (existingAccount != null) {
            // 기존 계정 업데이트
            existingAccount.apply {
                this.appKey = appKey
                this.appSecret = appSecret
                this.accountNumber = accountNumber
                this.accountAlias = accountAlias
            }
            kisAccountPort.save(existingAccount)
        } else {
            // 새 계정 생성
            val newAccount = KisAccount.create(
                userId = userId,
                appKey = appKey,
                appSecret = appSecret,
                accountNumber = accountNumber,
                environment = environment,
                accountAlias = accountAlias
            )
            kisAccountPort.save(newAccount)
        }
    }
    
    /**
     * KIS 계정 비활성화
     */
    fun deactivateKisAccount(userId: Long, environment: KisEnvironment) {
        kisAccountPort.findFirstByUserIdAndEnvironmentAndIsActiveTrueOrderByCreatedAtAsc(
            userId, environment
        ).ifPresent { account ->
            account.isActive = false
            kisAccountPort.save(account)
        }
    }
}