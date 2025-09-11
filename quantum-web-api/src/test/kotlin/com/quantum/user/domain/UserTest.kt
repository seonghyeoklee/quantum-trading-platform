package com.quantum.user.domain

import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import org.assertj.core.api.Assertions.*
import java.time.LocalDateTime

/**
 * User 도메인 엔티티 단위 테스트
 * 
 * 도메인 로직의 정확성을 검증하며, 비즈니스 규칙을 테스트
 */
class UserTest {

    private lateinit var user: User

    @BeforeEach
    fun setUp() {
        user = User(
            email = "test@quantum.local",
            name = "Test User",
            password = "password123",
            status = UserStatus.ACTIVE
        )
    }

    // ========== 생성 및 초기화 테스트 ==========

    @Test
    fun `User 생성 시 기본값들이 올바르게 설정된다`() {
        // Given & When
        val newUser = User(
            email = "new@test.com",
            name = "New User",
            password = "password"
        )

        // Then
        assertThat(newUser.email).isEqualTo("new@test.com")
        assertThat(newUser.name).isEqualTo("New User") 
        assertThat(newUser.password).isEqualTo("password")
        assertThat(newUser.status).isEqualTo(UserStatus.ACTIVE)
        assertThat(newUser.lastLoginAt).isNull()
        assertThat(newUser.roles).containsExactly(UserRole.USER)
        assertThat(newUser.getDomainEvents()).isEmpty()
    }

    // ========== 로그인 기능 테스트 ==========

    @Test
    fun `활성 사용자가 로그인하면 마지막 로그인 시간이 설정되고 도메인 이벤트가 발생한다`() {
        // Given
        val beforeLogin = LocalDateTime.now().minusMinutes(1)
        
        // When
        user.login()
        val afterLogin = LocalDateTime.now().plusMinutes(1)

        // Then
        assertThat(user.lastLoginAt).isNotNull()
        assertThat(user.lastLoginAt).isBetween(beforeLogin, afterLogin)
        
        val events = user.getDomainEvents()
        assertThat(events).hasSize(1)
        
        val loginEvent = events[0] as UserLoginEvent
        assertThat(loginEvent.userId).isEqualTo(user.id.toString())
        assertThat(loginEvent.email).isEqualTo("test@quantum.local")
        assertThat(loginEvent.loginTime).isEqualTo(user.lastLoginAt)
        assertThat(loginEvent.eventType).isEqualTo("USER_LOGIN")
    }

    @Test
    fun `비활성 사용자가 로그인 시도 시 예외가 발생한다`() {
        // Given
        user.status = UserStatus.INACTIVE

        // When & Then
        assertThrows<IllegalStateException> {
            user.login()
        }.also { exception ->
            assertThat(exception.message).isEqualTo("비활성 상태의 사용자입니다.")
        }

        // 마지막 로그인 시간이 설정되지 않음
        assertThat(user.lastLoginAt).isNull()
        assertThat(user.getDomainEvents()).isEmpty()
    }

    @Test
    fun `정지된 사용자가 로그인 시도 시 예외가 발생한다`() {
        // Given
        user.status = UserStatus.SUSPENDED

        // When & Then
        assertThrows<IllegalStateException> {
            user.login()
        }
    }

    // ========== 비밀번호 변경 테스트 ==========

    @Test
    fun `유효한 비밀번호로 변경할 수 있다`() {
        // Given
        val newPassword = "newPassword123"

        // When
        user.changePassword(newPassword)

        // Then
        assertThat(user.password).isEqualTo(newPassword)
    }

    @Test
    fun `6자 미만의 비밀번호 변경 시 예외가 발생한다`() {
        // Given
        val shortPassword = "12345"

        // When & Then
        assertThrows<IllegalArgumentException> {
            user.changePassword(shortPassword)
        }.also { exception ->
            assertThat(exception.message).isEqualTo("비밀번호는 최소 6자 이상이어야 합니다.")
        }

        // 기존 비밀번호가 유지됨
        assertThat(user.password).isEqualTo("password123")
    }

    // ========== 권한 관리 테스트 ==========

    @Test
    fun `사용자 권한을 추가할 수 있다`() {
        // Given & When
        user.addRole(UserRole.ADMIN)

        // Then
        assertThat(user.roles).contains(UserRole.USER, UserRole.ADMIN)
    }

    @Test
    fun `사용자 권한을 제거할 수 있다`() {
        // Given
        user.addRole(UserRole.ADMIN)
        user.addRole(UserRole.TRADER)

        // When
        user.removeRole(UserRole.ADMIN)

        // Then
        assertThat(user.roles).contains(UserRole.USER, UserRole.TRADER)
        assertThat(user.roles).doesNotContain(UserRole.ADMIN)
    }

    @Test
    fun `중복된 권한 추가는 무시된다`() {
        // Given & When
        user.addRole(UserRole.USER) // 이미 존재하는 권한

        // Then
        assertThat(user.roles).containsExactly(UserRole.USER)
        assertThat(user.roles).hasSize(1)
    }

    @Test
    fun `관리자 권한 여부를 확인할 수 있다`() {
        // Given & When - 초기에는 관리자가 아님
        assertThat(user.isAdmin()).isFalse()

        // When - 관리자 권한 추가
        user.addRole(UserRole.ADMIN)

        // Then
        assertThat(user.isAdmin()).isTrue()
    }

    // ========== 상태 관리 테스트 ==========

    @Test
    fun `사용자를 비활성화할 수 있다`() {
        // Given & When
        user.deactivate()

        // Then
        assertThat(user.status).isEqualTo(UserStatus.INACTIVE)
    }

    @Test
    fun `비활성화된 사용자를 다시 활성화할 수 있다`() {
        // Given
        user.deactivate()
        assertThat(user.status).isEqualTo(UserStatus.INACTIVE)

        // When
        user.activate()

        // Then
        assertThat(user.status).isEqualTo(UserStatus.ACTIVE)
    }

    // ========== 도메인 이벤트 관리 테스트 ==========

    @Test
    fun `도메인 이벤트를 클리어할 수 있다`() {
        // Given - 로그인으로 이벤트 생성
        user.login()
        assertThat(user.getDomainEvents()).hasSize(1)

        // When
        user.clearDomainEvents()

        // Then
        assertThat(user.getDomainEvents()).isEmpty()
    }

    @Test
    fun `여러 번 로그인하면 여러 개의 도메인 이벤트가 발생한다`() {
        // Given & When
        user.login()
        Thread.sleep(10) // 시간 차이를 위한 대기
        user.login()

        // Then
        assertThat(user.getDomainEvents()).hasSize(2)
        
        val events = user.getDomainEvents()
        assertThat(events.all { it is UserLoginEvent }).isTrue()
        assertThat(events.map { (it as UserLoginEvent).loginTime }).isSorted()
    }
}

/**
 * UserStatus enum 테스트
 */
class UserStatusTest {

    @Test
    fun `UserStatus enum 값들이 올바르게 정의되어 있다`() {
        assertThat(UserStatus.values()).containsExactly(
            UserStatus.ACTIVE,
            UserStatus.INACTIVE, 
            UserStatus.SUSPENDED
        )
    }
}

/**
 * UserRole enum 테스트
 */
class UserRoleTest {

    @Test
    fun `UserRole enum 값들이 올바르게 정의되어 있다`() {
        assertThat(UserRole.values()).containsExactly(
            UserRole.USER,
            UserRole.ADMIN,
            UserRole.TRADER
        )
    }
}

/**
 * UserLoginEvent 도메인 이벤트 테스트
 */
class UserLoginEventTest {

    @Test
    fun `UserLoginEvent가 올바르게 생성된다`() {
        // Given
        val userId = "user-123"
        val email = "test@quantum.local"
        val loginTime = LocalDateTime.now()

        // When
        val event = UserLoginEvent(userId, email, loginTime)

        // Then
        assertThat(event.eventId).isNotNull()
        assertThat(event.occurredAt).isNotNull()
        assertThat(event.aggregateId).isEqualTo(userId)
        assertThat(event.eventType).isEqualTo("USER_LOGIN")
        assertThat(event.userId).isEqualTo(userId)
        assertThat(event.email).isEqualTo(email)
        assertThat(event.loginTime).isEqualTo(loginTime)
    }
}