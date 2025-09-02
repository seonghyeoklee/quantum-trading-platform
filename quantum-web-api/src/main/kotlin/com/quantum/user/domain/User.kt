package com.quantum.user.domain

import com.quantum.common.BaseEntity
import com.quantum.common.DomainEvent
import jakarta.persistence.*
import java.time.LocalDateTime
import java.util.*

/**
 * User 애그리게이트 루트
 * DDD 패턴에 따른 사용자 도메인 엔티티
 */
@Entity
@Table(name = "users")
class User(
    @Column(nullable = false, unique = true)
    var email: String = "",
    
    @Column(nullable = false)
    var name: String = "",
    
    @Column(nullable = false)
    var password: String = "",
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    var status: UserStatus = UserStatus.ACTIVE
) : BaseEntity() {
    
    // JPA를 위한 기본 생성자
    protected constructor() : this("", "", "", UserStatus.ACTIVE)
    
    @ElementCollection(fetch = FetchType.EAGER)
    @Enumerated(EnumType.STRING)
    @CollectionTable(name = "user_roles", joinColumns = [JoinColumn(name = "user_id")])
    @Column(name = "role")
    var roles: MutableSet<UserRole> = mutableSetOf(UserRole.USER)
        private set
    
    @Column
    var lastLoginAt: LocalDateTime? = null
        private set
    
    // 도메인 이벤트를 위한 필드
    @Transient
    private val domainEvents = mutableListOf<DomainEvent>()
    
    /**
     * 로그인 처리
     */
    fun login() {
        if (status != UserStatus.ACTIVE) {
            throw IllegalStateException("비활성 상태의 사용자입니다.")
        }
        
        lastLoginAt = LocalDateTime.now()
        
        // 도메인 이벤트 발생
        domainEvents.add(UserLoginEvent(
            userId = id.toString(),
            email = email,
            loginTime = lastLoginAt!!
        ))
    }
    
    /**
     * 비밀번호 변경
     */
    fun changePassword(newPassword: String) {
        if (newPassword.length < 6) {
            throw IllegalArgumentException("비밀번호는 최소 6자 이상이어야 합니다.")
        }
        this.password = newPassword
    }
    
    /**
     * 사용자 권한 추가
     */
    fun addRole(role: UserRole) {
        roles.add(role)
    }
    
    /**
     * 사용자 권한 제거
     */
    fun removeRole(role: UserRole) {
        roles.remove(role)
    }
    
    /**
     * 사용자 비활성화
     */
    fun deactivate() {
        status = UserStatus.INACTIVE
    }
    
    /**
     * 사용자 활성화
     */
    fun activate() {
        status = UserStatus.ACTIVE
    }
    
    /**
     * 관리자 권한 확인
     */
    fun isAdmin(): Boolean {
        return roles.contains(UserRole.ADMIN)
    }
    
    /**
     * 도메인 이벤트 조회
     */
    fun getDomainEvents(): List<DomainEvent> = domainEvents.toList()
    
    /**
     * 도메인 이벤트 클리어
     */
    fun clearDomainEvents() {
        domainEvents.clear()
    }
}

/**
 * 사용자 상태
 */
enum class UserStatus {
    ACTIVE,     // 활성
    INACTIVE,   // 비활성
    SUSPENDED   // 정지
}

/**
 * 사용자 권한
 */
enum class UserRole {
    USER,       // 일반 사용자
    ADMIN,      // 관리자
    TRADER      // 트레이더 (향후 확장용)
}

/**
 * 사용자 로그인 도메인 이벤트
 */
data class UserLoginEvent(
    override val eventId: String = UUID.randomUUID().toString(),
    override val occurredAt: LocalDateTime = LocalDateTime.now(),
    override val aggregateId: String,
    override val eventType: String = "USER_LOGIN",
    val userId: String,
    val email: String,
    val loginTime: LocalDateTime
) : DomainEvent {
    constructor(userId: String, email: String, loginTime: LocalDateTime) : this(
        aggregateId = userId,
        userId = userId,
        email = email,
        loginTime = loginTime
    )
}