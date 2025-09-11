package com.quantum.user.infrastructure.persistence

import com.quantum.user.domain.User
import io.mockk.MockKAnnotations
import io.mockk.every
import io.mockk.impl.annotations.MockK
import io.mockk.verify
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import java.util.*

@DisplayName("UserRepositoryImpl 단위 테스트")
class UserRepositoryImplTest {

    @MockK
    private lateinit var userJpaRepository: UserJpaRepository

    private lateinit var userRepositoryImpl: UserRepositoryImpl

    private lateinit var testUser: User

    @BeforeEach
    fun setUp() {
        MockKAnnotations.init(this)
        userRepositoryImpl = UserRepositoryImpl(userJpaRepository)

        testUser = User(
            email = "test@quantum.local",
            password = "encodedPassword123",
            name = "Test User"
        )
    }

    @Test
    fun `사용자를 저장할 수 있다`() {
        // Given
        val savedUser = testUser.apply {
            javaClass.getDeclaredField("id").apply {
                isAccessible = true
                set(this@apply, 1L)
            }
        }
        every { userJpaRepository.save(testUser) } returns savedUser

        // When
        val result = userRepositoryImpl.save(testUser)

        // Then
        assertThat(result).isNotNull()
        assertThat(result.id).isEqualTo(1L)
        assertThat(result.email).isEqualTo("test@quantum.local")
        verify { userJpaRepository.save(testUser) }
    }

    @Test
    fun `ID로 사용자를 조회할 수 있다`() {
        // Given
        val userId = 1L
        every { userJpaRepository.findById(userId) } returns Optional.of(testUser)

        // When
        val result = userRepositoryImpl.findById(userId)

        // Then
        assertThat(result).isPresent()
        assertThat(result.get().email).isEqualTo("test@quantum.local")
        verify { userJpaRepository.findById(userId) }
    }

    @Test
    fun `존재하지 않는 ID로 조회하면 빈 Optional을 반환한다`() {
        // Given
        val userId = 999L
        every { userJpaRepository.findById(userId) } returns Optional.empty()

        // When
        val result = userRepositoryImpl.findById(userId)

        // Then
        assertThat(result).isEmpty()
        verify { userJpaRepository.findById(userId) }
    }

    @Test
    fun `이메일로 사용자를 조회할 수 있다`() {
        // Given
        val email = "test@quantum.local"
        every { userJpaRepository.findByEmail(email) } returns Optional.of(testUser)

        // When
        val result = userRepositoryImpl.findByEmail(email)

        // Then
        assertThat(result).isPresent()
        assertThat(result.get().email).isEqualTo(email)
        verify { userJpaRepository.findByEmail(email) }
    }

    @Test
    fun `존재하지 않는 이메일로 조회하면 빈 Optional을 반환한다`() {
        // Given
        val email = "nonexistent@quantum.local"
        every { userJpaRepository.findByEmail(email) } returns Optional.empty()

        // When
        val result = userRepositoryImpl.findByEmail(email)

        // Then
        assertThat(result).isEmpty()
        verify { userJpaRepository.findByEmail(email) }
    }

    @Test
    fun `이메일 존재 여부를 확인할 수 있다`() {
        // Given
        val existingEmail = "test@quantum.local"
        val nonExistingEmail = "nonexistent@quantum.local"
        
        every { userJpaRepository.existsByEmail(existingEmail) } returns true
        every { userJpaRepository.existsByEmail(nonExistingEmail) } returns false

        // When
        val existingResult = userRepositoryImpl.existsByEmail(existingEmail)
        val nonExistingResult = userRepositoryImpl.existsByEmail(nonExistingEmail)

        // Then
        assertThat(existingResult).isTrue()
        assertThat(nonExistingResult).isFalse()
        verify { userJpaRepository.existsByEmail(existingEmail) }
        verify { userJpaRepository.existsByEmail(nonExistingEmail) }
    }

    @Test
    fun `모든 사용자를 조회할 수 있다`() {
        // Given
        val user1 = User(email = "user1@quantum.local", password = "password", name = "User 1")
        val user2 = User(email = "user2@quantum.local", password = "password", name = "User 2")
        val allUsers = listOf(user1, user2)
        
        every { userJpaRepository.findAll() } returns allUsers

        // When
        val result = userRepositoryImpl.findAll()

        // Then
        assertThat(result).hasSize(2)
        assertThat(result.map { it.email }).containsExactlyInAnyOrder(
            "user1@quantum.local",
            "user2@quantum.local"
        )
        verify { userJpaRepository.findAll() }
    }

    @Test
    fun `사용자를 삭제할 수 있다`() {
        // Given
        every { userJpaRepository.delete(testUser) } returns Unit

        // When
        userRepositoryImpl.delete(testUser)

        // Then
        verify { userJpaRepository.delete(testUser) }
    }

    @Test
    fun `ID로 사용자를 삭제할 수 있다`() {
        // Given
        val userId = 1L
        every { userJpaRepository.deleteById(userId) } returns Unit

        // When
        userRepositoryImpl.deleteById(userId)

        // Then
        verify { userJpaRepository.deleteById(userId) }
    }

    @Test
    fun `repository 구현체가 올바른 포트 인터페이스를 구현한다`() {
        // When
        val repositoryType = userRepositoryImpl::class.java

        // Then
        assertThat(repositoryType.interfaces)
            .anyMatch { it.simpleName == "UserRepository" }
    }

    @Test
    fun `JPA repository 의존성이 올바르게 주입된다`() {
        // Given - setUp에서 MockK로 생성된 userJpaRepository

        // When
        val repositoryField = UserRepositoryImpl::class.java.getDeclaredField("userJpaRepository")
        repositoryField.isAccessible = true
        val injectedRepository = repositoryField.get(userRepositoryImpl)

        // Then
        assertThat(injectedRepository).isEqualTo(userJpaRepository)
    }

    @Test
    fun `사용자 저장 시 JPA repository 메서드가 한 번만 호출된다`() {
        // Given
        every { userJpaRepository.save(testUser) } returns testUser

        // When
        userRepositoryImpl.save(testUser)

        // Then
        verify(exactly = 1) { userJpaRepository.save(testUser) }
    }

    @Test
    fun `이메일 조회 시 JPA repository 메서드가 한 번만 호출된다`() {
        // Given
        val email = "test@quantum.local"
        every { userJpaRepository.findByEmail(email) } returns Optional.of(testUser)

        // When
        userRepositoryImpl.findByEmail(email)

        // Then
        verify(exactly = 1) { userJpaRepository.findByEmail(email) }
    }

    @Test
    fun `여러 번 조회해도 각각 JPA repository가 호출된다`() {
        // Given
        val email = "test@quantum.local"
        every { userJpaRepository.findByEmail(email) } returns Optional.of(testUser)

        // When
        userRepositoryImpl.findByEmail(email)
        userRepositoryImpl.findByEmail(email)
        userRepositoryImpl.findByEmail(email)

        // Then
        verify(exactly = 3) { userJpaRepository.findByEmail(email) }
    }
}