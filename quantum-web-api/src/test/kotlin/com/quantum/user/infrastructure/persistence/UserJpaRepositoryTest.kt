package com.quantum.user.infrastructure.persistence

import com.quantum.user.domain.User
import com.quantum.user.domain.UserStatus
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager
import org.springframework.test.context.ActiveProfiles

@DataJpaTest
@ActiveProfiles("test")
@DisplayName("UserJpaRepository 단위 테스트")
class UserJpaRepositoryTest {

    @Autowired
    private lateinit var repository: UserJpaRepository

    @Autowired
    private lateinit var entityManager: TestEntityManager

    private lateinit var testUser: User

    @BeforeEach
    fun setUp() {
        testUser = User(
            email = "test@quantum.local",
            password = "encodedPassword123",
            name = "Test User"
        )
    }

    @Test
    fun `이메일로 사용자를 조회할 수 있다`() {
        // Given
        entityManager.persistAndFlush(testUser)
        entityManager.clear()

        // When
        val found = repository.findByEmail("test@quantum.local")

        // Then
        assertThat(found).isPresent()
        assertThat(found.get().email).isEqualTo("test@quantum.local")
        assertThat(found.get().name).isEqualTo("Test User")
        assertThat(found.get().status).isEqualTo(UserStatus.ACTIVE)
    }

    @Test
    fun `존재하지 않는 이메일로 조회하면 빈 Optional을 반환한다`() {
        // When
        val found = repository.findByEmail("nonexistent@quantum.local")

        // Then
        assertThat(found).isEmpty()
    }

    @Test
    fun `이메일 존재 여부를 확인할 수 있다`() {
        // Given
        entityManager.persistAndFlush(testUser)

        // When & Then
        assertThat(repository.existsByEmail("test@quantum.local")).isTrue()
        assertThat(repository.existsByEmail("nonexistent@quantum.local")).isFalse()
    }

    @Test
    fun `활성 상태인 사용자 목록을 조회할 수 있다`() {
        // Given
        val activeUser1 = User(email = "active1@quantum.local", password = "password", name = "Active User 1")
        val activeUser2 = User(email = "active2@quantum.local", password = "password", name = "Active User 2")
        val inactiveUser = User(email = "inactive@quantum.local", password = "password", name = "Inactive User")
        inactiveUser.deactivate()

        entityManager.persistAndFlush(activeUser1)
        entityManager.persistAndFlush(activeUser2)
        entityManager.persistAndFlush(inactiveUser)

        // When
        val activeUsers = repository.findAllActiveUsers()

        // Then
        assertThat(activeUsers).hasSize(2)
        assertThat(activeUsers.map { it.email }).containsExactlyInAnyOrder(
            "active1@quantum.local",
            "active2@quantum.local"
        )
    }

    @Test
    fun `사용자 정보를 저장하고 수정할 수 있다`() {
        // Given
        val savedUser = repository.save(testUser)
        val userId = savedUser.id

        // When
        savedUser.name = "Updated Name"
        val updatedUser = repository.save(savedUser)

        // Then
        entityManager.clear()
        val foundUser = repository.findById(userId!!).orElse(null)
        assertThat(foundUser).isNotNull()
        assertThat(foundUser.name).isEqualTo("Updated Name")
        assertThat(foundUser.updatedAt).isAfter(foundUser.createdAt)
    }

    @Test
    fun `사용자를 삭제할 수 있다`() {
        // Given
        val savedUser = repository.save(testUser)
        val userId = savedUser.id!!

        // When
        repository.delete(savedUser)
        entityManager.flush()

        // Then
        val found = repository.findById(userId).orElse(null)
        assertThat(found).isNull()
    }

    @Test
    fun `페이징을 사용하여 사용자를 조회할 수 있다`() {
        // Given
        repeat(10) { index ->
            val user = User(email = "user$index@quantum.local", password = "password", name = "User $index")
            entityManager.persist(user)
        }
        entityManager.flush()

        // When
        val page = repository.findAll(org.springframework.data.domain.PageRequest.of(0, 5))

        // Then
        assertThat(page.content).hasSize(5)
        assertThat(page.totalElements).isEqualTo(10)
        assertThat(page.totalPages).isEqualTo(2)
    }

    @Test
    fun `사용자 총 개수를 조회할 수 있다`() {
        // Given
        repeat(5) { index ->
            val user = User(email = "user$index@quantum.local", password = "password", name = "User $index")
            entityManager.persist(user)
        }
        entityManager.flush()

        // When
        val count = repository.count()

        // Then
        assertThat(count).isEqualTo(5)
    }

    @Test
    fun `ID로 사용자를 조회할 수 있다`() {
        // Given
        val savedUser = repository.save(testUser)
        val userId = savedUser.id!!
        entityManager.clear()

        // When
        val found = repository.findById(userId)

        // Then
        assertThat(found).isPresent()
        assertThat(found.get().email).isEqualTo("test@quantum.local")
    }

    @Test
    fun `존재하지 않는 ID로 조회하면 빈 Optional을 반환한다`() {
        // When
        val found = repository.findById(999L)

        // Then
        assertThat(found).isEmpty()
    }
}