package com.quantum.kis.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import java.time.LocalDateTime

/**
 * 사용자 KIS API 설정 정보 도메인 엔티티
 * 
 * 유량 확장을 위한 다중 계좌 설정 지원
 * 계좌별 독립적 유량 관리
 */
@Entity
@Table(
    name = "user_kis_settings",
    uniqueConstraints = [
        UniqueConstraint(
            name = "uk_user_kis_env_account",
            columnNames = ["user_id", "environment", "account_number"]
        )
    ]
)
class UserKisSettings(
    /**
     * 사용자 ID (Foreign Key)
     */
    @Column(name = "user_id", nullable = false)
    var userId: Long = 0L,
    
    /**
     * KIS API 환경 (실전투자/모의투자)
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    var environment: KisEnvironment = KisEnvironment.SANDBOX,
    
    /**
     * KIS 앱키 (API 인증용)
     */
    @Column(name = "app_key", nullable = false, length = 100)
    var appKey: String = "",
    
    /**
     * KIS 앱시크릿 (API 인증용) - 암호화 저장 권장
     */
    @Column(name = "app_secret", nullable = false, length = 255)
    var appSecret: String = "",
    
    /**
     * HTS ID (웹소켓 체결통보용)
     */
    @Column(name = "hts_id", nullable = false, length = 50)
    var htsId: String = "",
    
    /**
     * 계좌번호
     */
    @Column(name = "account_number", nullable = false, length = 20)
    var accountNumber: String = "",
    
    /**
     * 상품코드 (보통 "01")
     */
    @Column(name = "product_code", nullable = false, length = 10)
    var productCode: String = "01",
    
    /**
     * 설정 목적 (기본 거래/유량 확장)
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    var purpose: KisSettingPurpose = KisSettingPurpose.PRIMARY_TRADING,
    
    /**
     * 설정 설명
     */
    @Column(length = 500)
    var description: String? = null,
    
    /**
     * 활성화 상태
     */
    @Column(name = "is_active", nullable = false)
    var isActive: Boolean = true,
    
    /**
     * 마지막 토큰 갱신 시간
     */
    @Column(name = "last_token_refresh_at")
    var lastTokenRefreshAt: LocalDateTime? = null

) : BaseEntity() {
    
    /**
     * JPA를 위한 기본 생성자
     */
    protected constructor() : this(
        userId = 0L,
        environment = KisEnvironment.SANDBOX,
        appKey = "",
        appSecret = "",
        htsId = "",
        accountNumber = "",
        productCode = "01"
    )
    
    /**
     * 해당 환경의 유량 제한 정책 조회
     */
    fun getRateLimit(): KisRateLimit = KisRateLimit.forEnvironment(environment)
    
    /**
     * 설정이 유효한지 검증
     */
    fun validateSettings(): Boolean {
        return appKey.isNotBlank() && 
               appSecret.isNotBlank() && 
               htsId.isNotBlank() && 
               accountNumber.isNotBlank() &&
               isActive
    }
    
    /**
     * 토큰 갱신 시간 업데이트
     */
    fun updateTokenRefreshTime() {
        lastTokenRefreshAt = LocalDateTime.now()
    }
    
    /**
     * 설정 비활성화
     */
    fun deactivate(reason: String = "사용자 요청") {
        isActive = false
        description = "$description [비활성화: $reason]"
    }
    
    /**
     * 설정 활성화
     */
    fun activate() {
        if (!validateSettings()) {
            throw IllegalStateException("설정 정보가 완전하지 않아 활성화할 수 없습니다.")
        }
        isActive = true
    }
}

/**
 * KIS 설정 목적
 */
enum class KisSettingPurpose(
    val displayName: String,
    val description: String
) {
    /**
     * 기본 거래용 계좌
     */
    PRIMARY_TRADING("기본거래", "주요 거래를 위한 기본 계좌"),
    
    /**
     * 유량 확장용 계좌
     */
    RATE_LIMIT_EXPANSION("유량확장", "API 호출 유량 확장을 위한 추가 계좌"),
    
    /**
     * 실시간 데이터 전용 계좌
     */
    REALTIME_DATA_ONLY("실시간전용", "실시간 데이터 수신 전용 계좌"),
    
    /**
     * 백업 계좌
     */
    BACKUP("백업", "장애시 사용할 백업 계좌")
}