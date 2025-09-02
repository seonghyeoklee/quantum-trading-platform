package com.quantum.kis.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import org.hibernate.annotations.Comment
import java.time.LocalDateTime

/**
 * KIS 계정 정보 도메인 엔티티
 * 
 * 사용자별 KIS 계정 정보를 암호화하여 안전하게 저장
 * 하이브리드 토큰 아키텍처에서 토큰 발급의 기본 정보 제공
 */
@Entity
@Table(
    name = "kis_accounts",
    indexes = [
        Index(name = "idx_kis_account_user_env", columnList = "user_id, environment"),
        Index(name = "idx_kis_account_app_key", columnList = "app_key"),
        Index(name = "idx_kis_account_active", columnList = "is_active")
    ]
)
@Comment("KIS 계정 정보")
class KisAccount(
    /**
     * 사용자 ID (Foreign Key)
     */
    @Column(name = "user_id", nullable = false)
    @Comment("사용자 ID")
    var userId: Long = 0L,
    
    /**
     * KIS API App Key (암호화 저장)
     */
    @Column(name = "app_key", nullable = false, length = 500)
    @Comment("KIS API 앱키 (암호화 저장)")
    var appKey: String = "",
    
    /**
     * KIS API App Secret (암호화 저장)
     */
    @Column(name = "app_secret", nullable = false, length = 500)
    @Comment("KIS API 앱시크릿 (암호화 저장)")
    var appSecret: String = "",
    
    /**
     * 계좌번호 (암호화 저장)
     */
    @Column(name = "account_number", nullable = false, length = 200)
    @Comment("계좌번호 (암호화 저장)")
    var accountNumber: String = "",
    
    /**
     * KIS 환경 (LIVE, SANDBOX)
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "environment", nullable = false, length = 20)
    @Comment("KIS 환경 (LIVE, SANDBOX)")
    var environment: KisEnvironment = KisEnvironment.SANDBOX,
    
    /**
     * 계정 활성화 상태
     */
    @Column(name = "is_active", nullable = false)
    @Comment("계정 활성화 상태")
    var isActive: Boolean = true,
    
    /**
     * 계정 별칭 (사용자가 구분하기 위한 이름)
     */
    @Column(name = "account_alias", length = 100)
    @Comment("계정 별칭")
    var accountAlias: String? = null,
    
    /**
     * 마지막 토큰 발급 시간
     */
    @Column(name = "last_token_issued_at")
    @Comment("마지막 토큰 발급 시간")
    var lastTokenIssuedAt: LocalDateTime? = null,
    
    /**
     * 마지막 검증 시간
     */
    @Column(name = "last_validated_at")
    @Comment("마지막 검증 시간")
    var lastValidatedAt: LocalDateTime? = null

) : BaseEntity() {
    
    /**
     * JPA를 위한 기본 생성자
     */
    protected constructor() : this(
        userId = 0L,
        environment = KisEnvironment.SANDBOX
    )
    
    /**
     * 계정 정보 검증
     */
    fun validateAccountInfo() {
        require(userId > 0) { "사용자 ID는 필수입니다." }
        require(appKey.isNotBlank()) { "App Key는 필수입니다." }
        require(appSecret.isNotBlank()) { "App Secret은 필수입니다." }
        require(accountNumber.isNotBlank()) { "계좌번호는 필수입니다." }
        require(isValidAccountNumber(accountNumber)) { "올바르지 않은 계좌번호 형식입니다." }
    }
    
    /**
     * 계좌번호 형식 검증 (한국투자증권 형식: 12345678-01)
     */
    private fun isValidAccountNumber(accountNumber: String): Boolean {
        val pattern = "^\\d{8}-\\d{2}$".toRegex()
        return pattern.matches(accountNumber)
    }
    
    /**
     * 계정 활성화
     */
    fun activate() {
        this.isActive = true
        this.lastValidatedAt = LocalDateTime.now()
    }
    
    /**
     * 계정 비활성화
     */
    fun deactivate() {
        this.isActive = false
    }
    
    /**
     * 토큰 발급 완료 표시
     */
    fun markTokenIssued() {
        this.lastTokenIssuedAt = LocalDateTime.now()
    }
    
    /**
     * 계정 검증 완료 표시
     */
    fun markValidated() {
        this.lastValidatedAt = LocalDateTime.now()
    }
    
    /**
     * 계정 식별 정보 생성
     */
    fun getAccountIdentifier(): String {
        return "${environment.name}_${accountNumber}_${userId}"
    }
    
    /**
     * 표시용 계정 정보
     */
    fun getDisplayInfo(): String {
        val alias = if (accountAlias.isNullOrBlank()) accountNumber else accountAlias!!
        return "$alias (${environment.displayName})"
    }
    
    /**
     * 보안을 위한 마스킹된 계정번호
     */
    fun getMaskedAccountNumber(): String {
        return if (accountNumber.length >= 8) {
            "${accountNumber.substring(0, 4)}****${accountNumber.substring(accountNumber.length - 2)}"
        } else {
            "****"
        }
    }
    
    /**
     * 보안을 위한 마스킹된 App Key
     */
    fun getMaskedAppKey(): String {
        return if (appKey.length >= 8) {
            "${appKey.substring(0, 4)}${"*".repeat(appKey.length - 8)}${appKey.substring(appKey.length - 4)}"
        } else {
            "*".repeat(appKey.length)
        }
    }
    
    /**
     * 토큰 발급 가능 여부 확인
     */
    fun canIssueToken(): Boolean {
        return isActive && appKey.isNotBlank() && appSecret.isNotBlank()
    }
    
    companion object {
        /**
         * KIS 계정 생성을 위한 팩토리 메서드
         */
        fun create(
            userId: Long,
            appKey: String,
            appSecret: String,
            accountNumber: String,
            environment: KisEnvironment,
            accountAlias: String? = null
        ): KisAccount {
            val account = KisAccount(
                userId = userId,
                appKey = appKey,
                appSecret = appSecret,
                accountNumber = accountNumber,
                environment = environment,
                accountAlias = accountAlias,
                isActive = true
            )
            
            account.validateAccountInfo()
            return account
        }
        
        /**
         * 테스트용 계정 생성
         */
        fun createForTesting(
            userId: Long = 1L,
            environment: KisEnvironment = KisEnvironment.SANDBOX,
            accountNumber: String = "12345678-01"
        ): KisAccount {
            return create(
                userId = userId,
                appKey = "test_app_key",
                appSecret = "test_app_secret", 
                accountNumber = accountNumber,
                environment = environment,
                accountAlias = "테스트 계정"
            )
        }
    }
}