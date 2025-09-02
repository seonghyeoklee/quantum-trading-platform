package com.quantum.kis.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import org.hibernate.annotations.Comment
import java.time.Duration
import java.time.LocalDateTime

/**
 * KIS 액세스 토큰 도메인 엔티티
 * 
 * 하이브리드 토큰 아키텍처에서 KIS API 호출을 위한 액세스 토큰 관리
 * 6시간 유효기간, 자동 갱신 지원
 */
@Entity
@Table(
    name = "kis_tokens",
    indexes = [
        Index(name = "idx_kis_token_user_env", columnList = "user_id, environment"),
        Index(name = "idx_kis_token_account", columnList = "kis_account_id"),
        Index(name = "idx_kis_token_status", columnList = "status"),
        Index(name = "idx_kis_token_expires", columnList = "expires_at"),
        Index(name = "idx_kis_token_refresh", columnList = "expires_at, status")
    ]
)
@Comment("KIS 액세스 토큰")
class KisToken(
    /**
     * 사용자 ID (Foreign Key)
     */
    @Column(name = "user_id", nullable = false)
    @Comment("사용자 ID")
    var userId: Long = 0L,
    
    /**
     * KIS 계정 ID (Foreign Key)
     */
    @Column(name = "kis_account_id", nullable = false)
    @Comment("KIS 계정 ID")
    var kisAccountId: Long = 0L,
    
    /**
     * KIS 액세스 토큰 (암호화 저장)
     */
    @Column(name = "access_token", nullable = false, length = 2048)
    @Comment("KIS 액세스 토큰 (암호화 저장)")
    var accessToken: String = "",
    
    /**
     * 토큰 만료 시간 (UTC)
     */
    @Column(name = "expires_at", nullable = false)
    @Comment("토큰 만료 시간")
    var expiresAt: LocalDateTime = LocalDateTime.now().plusHours(6),
    
    /**
     * KIS 환경 (LIVE, SANDBOX)
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "environment", nullable = false, length = 20)
    @Comment("KIS 환경 (LIVE, SANDBOX)")
    var environment: KisEnvironment = KisEnvironment.SANDBOX,
    
    /**
     * 토큰 상태 (ACTIVE, EXPIRED, REVOKED 등)
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    @Comment("토큰 상태 (ACTIVE, EXPIRED, REVOKED)")
    var status: TokenStatus = TokenStatus.ACTIVE,
    
    /**
     * 토큰 타입 (Bearer 고정)
     */
    @Column(name = "token_type", nullable = false, length = 20)
    @Comment("토큰 타입 (Bearer)")
    var tokenType: String = "Bearer",
    
    /**
     * 마지막 사용 시간
     */
    @Column(name = "last_used_at")
    @Comment("마지막 사용 시간")
    var lastUsedAt: LocalDateTime? = null,
    
    /**
     * 토큰 갱신 횟수
     */
    @Column(name = "refresh_count", nullable = false)
    @Comment("토큰 갱신 횟수")
    var refreshCount: Int = 0,
    
    /**
     * 다음 자동 갱신 시간 (만료 1시간 전)
     */
    @Column(name = "next_refresh_at")
    @Comment("다음 자동 갱신 시간")
    var nextRefreshAt: LocalDateTime? = null

) : BaseEntity() {
    
    /**
     * JPA를 위한 기본 생성자
     */
    protected constructor() : this(
        userId = 0L,
        kisAccountId = 0L,
        environment = KisEnvironment.SANDBOX
    )
    
    init {
        // 생성 시 자동으로 다음 갱신 시간 설정 (만료 1시간 전)
        calculateNextRefreshTime()
    }
    
    /**
     * 토큰 검증
     */
    fun validateToken() {
        require(userId > 0) { "사용자 ID는 필수입니다." }
        require(kisAccountId > 0) { "KIS 계정 ID는 필수입니다." }
        require(accessToken.isNotBlank()) { "액세스 토큰은 필수입니다." }
        require(expiresAt.isAfter(LocalDateTime.now())) { "만료 시간은 현재 시간보다 이후여야 합니다." }
    }
    
    /**
     * 토큰이 만료되었는지 확인
     */
    fun isExpired(): Boolean {
        return LocalDateTime.now().isAfter(expiresAt)
    }
    
    /**
     * 토큰이 곧 만료될 예정인지 확인 (1시간 이내)
     */
    fun isNearExpiry(thresholdMinutes: Long = 60): Boolean {
        val threshold = LocalDateTime.now().plusMinutes(thresholdMinutes)
        return expiresAt.isBefore(threshold)
    }
    
    /**
     * 토큰이 사용 가능한 상태인지 확인
     */
    fun isUsable(): Boolean {
        return status.isUsable() && !isExpired()
    }
    
    /**
     * 토큰 갱신이 필요한지 확인
     */
    fun needsRefresh(): Boolean {
        return status.needsRefresh() || isExpired() || isNearExpiry()
    }
    
    /**
     * 토큰을 만료 상태로 변경
     */
    fun expire() {
        this.status = TokenStatus.EXPIRED
    }
    
    /**
     * 토큰을 폐기 상태로 변경
     */
    fun revoke() {
        this.status = TokenStatus.REVOKED
    }
    
    /**
     * 토큰 갱신 시작
     */
    fun startRefresh() {
        this.status = TokenStatus.REFRESHING
    }
    
    /**
     * 토큰 갱신 완료
     */
    fun completeRefresh(newAccessToken: String, newExpiresAt: LocalDateTime) {
        this.accessToken = newAccessToken
        this.expiresAt = newExpiresAt
        this.status = TokenStatus.ACTIVE
        this.refreshCount += 1
        calculateNextRefreshTime()
    }
    
    /**
     * 토큰 갱신 실패
     */
    fun failRefresh() {
        this.status = TokenStatus.ERROR
    }
    
    /**
     * 토큰 사용 기록
     */
    fun markUsed() {
        this.lastUsedAt = LocalDateTime.now()
    }
    
    /**
     * 다음 자동 갱신 시간 계산 (만료 1시간 전)
     */
    private fun calculateNextRefreshTime() {
        this.nextRefreshAt = expiresAt.minusHours(1)
    }
    
    /**
     * 토큰의 남은 유효 시간 계산
     */
    fun getRemainingTime(): Duration {
        return Duration.between(LocalDateTime.now(), expiresAt).let { duration ->
            if (duration.isNegative) Duration.ZERO else duration
        }
    }
    
    /**
     * 토큰 사용율 계산 (0.0 ~ 1.0)
     */
    fun getUsageRatio(): Double {
        val totalDuration = Duration.between(createdAt, expiresAt)
        val usedDuration = Duration.between(createdAt, LocalDateTime.now())
        
        return if (totalDuration.toMillis() == 0L) 1.0 
               else (usedDuration.toMillis().toDouble() / totalDuration.toMillis()).coerceIn(0.0, 1.0)
    }
    
    /**
     * Authorization 헤더 값 생성
     */
    fun getAuthorizationHeader(): String {
        return "$tokenType $accessToken"
    }
    
    /**
     * 토큰 요약 정보
     */
    fun getSummary(): String {
        val remainingTime = getRemainingTime()
        val hours = remainingTime.toHours()
        val minutes = remainingTime.toMinutesPart()
        
        return "${environment.displayName} 토큰 (${status.displayName}) - 남은시간: ${hours}h ${minutes}m"
    }
    
    companion object {
        /**
         * 새 토큰 생성을 위한 팩토리 메서드
         */
        fun create(
            userId: Long,
            kisAccountId: Long,
            accessToken: String,
            environment: KisEnvironment,
            expiresAt: LocalDateTime = LocalDateTime.now().plusHours(6)
        ): KisToken {
            val token = KisToken(
                userId = userId,
                kisAccountId = kisAccountId,
                accessToken = accessToken,
                expiresAt = expiresAt,
                environment = environment,
                status = TokenStatus.ACTIVE,
                tokenType = "Bearer"
            )
            
            token.validateToken()
            return token
        }
        
        /**
         * 테스트용 토큰 생성
         */
        fun createForTesting(
            userId: Long = 1L,
            kisAccountId: Long = 1L,
            environment: KisEnvironment = KisEnvironment.SANDBOX,
            accessToken: String = "test_access_token_12345"
        ): KisToken {
            return create(
                userId = userId,
                kisAccountId = kisAccountId,
                accessToken = accessToken,
                environment = environment
            )
        }
        
        /**
         * 만료된 토큰 생성 (테스트용)
         */
        fun createExpiredForTesting(
            userId: Long = 1L,
            kisAccountId: Long = 1L,
            environment: KisEnvironment = KisEnvironment.SANDBOX
        ): KisToken {
            val token = create(
                userId = userId,
                kisAccountId = kisAccountId,
                accessToken = "expired_token_12345",
                environment = environment,
                expiresAt = LocalDateTime.now().minusHours(1)
            )
            token.expire()
            return token
        }
    }
}