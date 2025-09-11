package com.quantum.user.application.usecase

import com.quantum.user.application.port.incoming.AuthUseCase
import com.quantum.user.application.port.incoming.LoginCommand
import com.quantum.user.domain.User
import com.quantum.user.domain.UserRole
import com.quantum.user.domain.UserStatus
import com.quantum.user.application.port.outgoing.UserRepository
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.security.crypto.password.PasswordEncoder
import org.springframework.test.context.ActiveProfiles
import org.springframework.transaction.annotation.Transactional
import org.assertj.core.api.Assertions.*

/**
 * AuthUseCase 통합 테스트
 * 
 * Spring Boot 컨텍스트를 사용한 애플리케이션 계층 테스트
 * 실제 의존성을 사용하여 UseCase의 전체 흐름을 검증
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
class AuthUseCaseSimpleTest {

    @Autowired
    private lateinit var authUseCase: AuthUseCase

    @Autowired 
    private lateinit var userRepository: UserRepository

    @Autowired
    private lateinit var passwordEncoder: PasswordEncoder

    private lateinit var testUser: User

    @BeforeEach
    fun setUp() {
        // 테스트용 사용자 생성
        testUser = User(
            email = "test@quantum.local",
            name = "Test User", 
            password = passwordEncoder.encode("password123"),
            status = UserStatus.ACTIVE
        )
        testUser.addRole(UserRole.USER)
        userRepository.save(testUser)
    }

    // ========== 로그인 성공 시나리오 ==========

    @Test
    fun `유효한 사용자 정보로 로그인이 성공한다`() {
        // Given
        val loginCommand = LoginCommand(
            email = "test@quantum.local",
            password = "password123"
        )

        // When
        val result = authUseCase.login(loginCommand)

        // Then
        assertThat(result.success).isTrue()
        assertThat(result.accessToken).isNotNull()
        assertThat(result.expiresIn).isEqualTo(86400L)
        assertThat(result.user).isNotNull()
        assertThat(result.user!!.email).isEqualTo("test@quantum.local")
        assertThat(result.user!!.name).isEqualTo("Test User")
        assertThat(result.errorMessage).isNull()
    }

    // ========== 로그인 실패 시나리오 ==========

    @Test
    fun `잘못된 이메일 형식으로 로그인 실패`() {
        // Given
        val loginCommand = LoginCommand(
            email = "invalid-email",
            password = "password123"
        )

        // When
        val result = authUseCase.login(loginCommand)

        // Then
        assertThat(result.success).isFalse()
        assertThat(result.errorMessage).isEqualTo("올바르지 않은 이메일 형식입니다.")
        assertThat(result.accessToken).isNull()
        assertThat(result.user).isNull()
    }

    @Test
    fun `존재하지 않는 사용자로 로그인 실패`() {
        // Given
        val loginCommand = LoginCommand(
            email = "nonexistent@quantum.local",
            password = "password123"
        )

        // When
        val result = authUseCase.login(loginCommand)

        // Then
        assertThat(result.success).isFalse()
        assertThat(result.errorMessage).isEqualTo("이메일 또는 비밀번호가 올바르지 않습니다.")
        assertThat(result.accessToken).isNull()
        assertThat(result.user).isNull()
    }

    @Test
    fun `잘못된 비밀번호로 로그인 실패`() {
        // Given
        val loginCommand = LoginCommand(
            email = "test@quantum.local",
            password = "wrongpassword"
        )

        // When
        val result = authUseCase.login(loginCommand)

        // Then
        assertThat(result.success).isFalse()
        assertThat(result.errorMessage).isEqualTo("이메일 또는 비밀번호가 올바르지 않습니다.")
        assertThat(result.accessToken).isNull()
        assertThat(result.user).isNull()
    }

    @Test
    fun `비활성 사용자 로그인 실패`() {
        // Given - 비활성 사용자 생성
        val inactiveUser = User(
            email = "inactive@quantum.local",
            name = "Inactive User",
            password = passwordEncoder.encode("password123"),
            status = UserStatus.INACTIVE
        )
        userRepository.save(inactiveUser)

        val loginCommand = LoginCommand(
            email = "inactive@quantum.local",
            password = "password123"
        )

        // When
        val result = authUseCase.login(loginCommand)

        // Then
        assertThat(result.success).isFalse()
        assertThat(result.errorMessage).contains("오류가 발생했습니다")
        assertThat(result.accessToken).isNull()
        assertThat(result.user).isNull()
    }

    // ========== 사용자 정보 조회 테스트 ==========

    @Test
    fun `사용자 ID로 정보를 조회할 수 있다`() {
        // Given
        val userId = testUser.id

        // When
        val result = authUseCase.getUserInfo(userId)

        // Then
        assertThat(result.id).isEqualTo(userId)
        assertThat(result.email).isEqualTo("test@quantum.local")
        assertThat(result.name).isEqualTo("Test User")
    }

    @Test
    fun `존재하지 않는 사용자 ID 조회 시 예외 발생`() {
        // Given
        val nonExistentUserId = 999999L

        // When & Then
        assertThatThrownBy {
            authUseCase.getUserInfo(nonExistentUserId)
        }.isInstanceOf(RuntimeException::class.java)
         .hasMessageContaining("사용자를 찾을 수 없습니다")
    }

    // ========== 로그아웃 테스트 ==========

    @Test
    fun `로그아웃이 성공적으로 처리된다`() {
        // Given
        val userId = testUser.id

        // When
        val result = authUseCase.logout(userId)

        // Then
        assertThat(result.message).isEqualTo("로그아웃 완료")
    }

    // ========== 도메인 이벤트 검증 테스트 ==========

    @Test
    fun `로그인 성공 시 사용자 도메인에서 로그인 이벤트가 발생한다`() {
        // Given
        val loginCommand = LoginCommand(
            email = "test@quantum.local",
            password = "password123"
        )

        // When
        val result = authUseCase.login(loginCommand)

        // Then
        assertThat(result.success).isTrue()
        
        // 로그인 후 사용자 정보 다시 조회해서 lastLoginAt 확인
        val updatedUser = userRepository.findById(testUser.id).orElseThrow()
        assertThat(updatedUser.lastLoginAt).isNotNull()
    }
}