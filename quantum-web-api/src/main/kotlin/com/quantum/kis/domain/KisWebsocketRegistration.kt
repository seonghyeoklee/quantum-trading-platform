package com.quantum.kis.domain

import com.quantum.common.BaseEntity
import jakarta.persistence.*
import java.time.LocalDateTime

/**
 * KIS 웹소켓 실시간 데이터 등록 현황 관리
 * 
 * 세션당 최대 41개 실시간 데이터 등록 제한 관리
 */
@Entity
@Table(
    name = "kis_websocket_registrations",
    indexes = [
        Index(name = "idx_kis_websocket_setting_active", columnList = "kis_setting_id, is_active"),
        Index(name = "idx_kis_websocket_data_type", columnList = "data_type, is_active")
    ]
)
class KisWebsocketRegistration(
    /**
     * KIS 설정 ID (Foreign Key)
     */
    @Column(name = "kis_setting_id", nullable = false)
    var kisSettingId: Long = 0L,
    
    /**
     * 실시간 데이터 유형
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "data_type", nullable = false, length = 50)
    var dataType: WebsocketDataType = WebsocketDataType.REAL_TIME_PRICE,
    
    /**
     * 종목코드 (체결통보 제외)
     */
    @Column(length = 20)
    var symbol: String? = null,
    
    /**
     * HTS ID (체결통보용)
     */
    @Column(name = "hts_id", length = 50)
    var htsId: String? = null,
    
    /**
     * 등록 활성화 상태
     */
    @Column(name = "is_active", nullable = false)
    var isActive: Boolean = true,
    
    /**
     * 등록 시간
     */
    @Column(name = "registered_at", nullable = false)
    var registeredAt: LocalDateTime = LocalDateTime.now(),
    
    /**
     * 등록 해제 시간
     */
    @Column(name = "unregistered_at")
    var unregisteredAt: LocalDateTime? = null

) : BaseEntity() {
    
    /**
     * JPA를 위한 기본 생성자
     */
    protected constructor() : this(
        kisSettingId = 0L,
        dataType = WebsocketDataType.REAL_TIME_PRICE
    )
    
    /**
     * 등록 데이터 유효성 검증
     */
    private fun validateRegistrationData() {
        when (dataType) {
            WebsocketDataType.ORDER_NOTIFICATION -> {
                require(htsId != null && symbol == null) {
                    "체결통보 등록시 HTS ID는 필수이고 종목코드는 불필요합니다."
                }
            }
            else -> {
                require(symbol != null && htsId == null) {
                    "${dataType.displayName} 등록시 종목코드는 필수이고 HTS ID는 불필요합니다."
                }
            }
        }
    }
    
    /**
     * 등록 해제
     */
    fun unregister() {
        if (!isActive) {
            throw IllegalStateException("이미 해제된 등록입니다.")
        }
        
        isActive = false
        unregisteredAt = LocalDateTime.now()
    }
    
    /**
     * 등록 키 생성 (중복 방지용)
     */
    fun getRegistrationKey(): String {
        return when (dataType) {
            WebsocketDataType.ORDER_NOTIFICATION -> "${dataType.name}:$htsId"
            else -> "${dataType.name}:$symbol"
        }
    }
    
    /**
     * 등록 설명 생성
     */
    fun getDescription(): String {
        return when (dataType) {
            WebsocketDataType.ORDER_NOTIFICATION -> "${dataType.displayName} (HTS: $htsId)"
            else -> "${dataType.displayName} ($symbol)"
        }
    }
    
    companion object {
        /**
         * 실시간 체결가 등록 생성
         */
        fun createRealtimePrice(kisSettingId: Long, symbol: String): KisWebsocketRegistration {
            val registration = KisWebsocketRegistration(
                kisSettingId = kisSettingId,
                dataType = WebsocketDataType.REAL_TIME_PRICE,
                symbol = symbol
            )
            registration.validateRegistrationData()
            return registration
        }
        
        /**
         * 호가 등록 생성
         */
        fun createQuote(kisSettingId: Long, symbol: String): KisWebsocketRegistration {
            val registration = KisWebsocketRegistration(
                kisSettingId = kisSettingId,
                dataType = WebsocketDataType.QUOTE,
                symbol = symbol
            )
            registration.validateRegistrationData()
            return registration
        }
        
        /**
         * 예상체결 등록 생성
         */
        fun createExpectedPrice(kisSettingId: Long, symbol: String): KisWebsocketRegistration {
            val registration = KisWebsocketRegistration(
                kisSettingId = kisSettingId,
                dataType = WebsocketDataType.EXPECTED_PRICE,
                symbol = symbol
            )
            registration.validateRegistrationData()
            return registration
        }
        
        /**
         * 체결통보 등록 생성
         */
        fun createOrderNotification(kisSettingId: Long, htsId: String): KisWebsocketRegistration {
            val registration = KisWebsocketRegistration(
                kisSettingId = kisSettingId,
                dataType = WebsocketDataType.ORDER_NOTIFICATION,
                htsId = htsId
            )
            registration.validateRegistrationData()
            return registration
        }
    }
}

/**
 * 웹소켓 실시간 데이터 유형
 */
enum class WebsocketDataType(
    val displayName: String,
    val description: String
) {
    /**
     * 실시간 체결가
     */
    REAL_TIME_PRICE("실시간체결가", "종목의 실시간 체결 가격 정보"),
    
    /**
     * 호가 정보
     */
    QUOTE("호가", "종목의 매수/매도 호가 정보"),
    
    /**
     * 예상체결 정보
     */
    EXPECTED_PRICE("예상체결", "장 시작 전 예상 체결 가격"),
    
    /**
     * 체결통보 (HTS ID 기반)
     */
    ORDER_NOTIFICATION("체결통보", "사용자 주문의 체결 통보")
}