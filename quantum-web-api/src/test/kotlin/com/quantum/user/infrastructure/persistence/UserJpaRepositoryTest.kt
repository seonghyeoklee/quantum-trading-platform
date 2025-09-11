package com.quantum.user.infrastructure.persistence

import com.quantum.user.domain.User
import com.quantum.user.domain.UserRole
import com.quantum.user.domain.UserStatus
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager
import org.springframework.test.context.ActiveProfiles
import java.time.LocalDateTime

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
        testUser = User.create(
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
        assertThat(found).isNotNull()
        assertThat(found!!.email).isEqualTo("test@quantum.local")
        assertThat(found.name).isEqualTo("Test User")
        assertThat(found.status).isEqualTo(UserStatus.ACTIVE)
    }

    @Test
    fun `존재하지 않는 이메일로 조회하면 null을 반환한다`() {
        // When
        val found = repository.findByEmail("nonexistent@quantum.local")

        // Then
        assertThat(found).isNull()
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
        val activeUser1 = User.create("active1@quantum.local", "password", "Active User 1")
        val activeUser2 = User.create("active2@quantum.local", "password", "Active User 2")
        val inactiveUser = User.create("inactive@quantum.local", "password", "Inactive User")
        inactiveUser.deactivate()

        entityManager.persistAndFlush(activeUser1)
        entityManager.persistAndFlush(activeUser2)
        entityManager.persistAndFlush(inactiveUser)

        // When
        val activeUsers = repository.findByStatus(UserStatus.ACTIVE)

        // Then
        assertThat(activeUsers).hasSize(2)
        assertThat(activeUsers.map { it.email }).containsExactlyInAnyOrder(
            "active1@quantum.local",
            "active2@quantum.local"
        )
    }

    @Test
    fun `특정 날짜 이후 마지막 로그인한 사용자를 조회할 수 있다`() {
        // Given
        val recentUser = User.create("recent@quantum.local", "password", "Recent User")
        recentUser.login() // 최근 로그인

        val oldUser = User.create("old@quantum.local", "password", "Old User")
        
        entityManager.persistAndFlush(recentUser)
        entityManager.persistAndFlush(oldUser)
        entityManager.clear()

        val cutoffDate = LocalDateTime.now().minusHours(1)

        // When
        val recentUsers = repository.findByLastLoginAtAfter(cutoffDate)

        // Then
        assertThat(recentUsers).hasSize(1)
        assertThat(recentUsers[0].email).isEqualTo("recent@quantum.local")
    }

    @Test
    fun `역할별로 사용자를 조회할 수 있다`() {
        // Given
        val adminUser = User.create("admin@quantum.local", "password", "Admin User")
        adminUser.grantRole(UserRole.ADMIN)

        val regularUser = User.create("user@quantum.local", "password", "Regular User")

        entityManager.persistAndFlush(adminUser)
        entityManager.persistAndFlush(regularUser)

        // When
        val adminUsers = repository.findByRoles(UserRole.ADMIN)

        // Then
        assertThat(adminUsers).hasSize(1)
        assertThat(adminUsers[0].email).isEqualTo("admin@quantum.local")
    }

    @Test
    fun `사용자 정보를 저장하고 수정할 수 있다`() {
        // Given
        val savedUser = repository.save(testUser)
        val userId = savedUser.id

        // When
        savedUser.updateProfile("Updated Name")
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
            val user = User.create("user$index@quantum.local", "password", "User $index")
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
}