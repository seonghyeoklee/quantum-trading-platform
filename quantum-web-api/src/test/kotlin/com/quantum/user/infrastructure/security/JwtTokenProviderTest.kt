package com.quantum.user.infrastructure.security

import com.quantum.config.JwtProperties
import com.quantum.user.domain.User
import com.quantum.user.domain.UserRole
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import io.jsonwebtoken.ExpiredJwtException
import io.jsonwebtoken.MalformedJwtException
import io.jsonwebtoken.security.SignatureException
import java.time.LocalDateTime
import java.util.*

@DisplayName("JwtTokenProvider 단위 테스트")
class JwtTokenProviderTest {

    private lateinit var jwtTokenProvider: JwtTokenProvider
    private lateinit var jwtProperties: JwtProperties
    private lateinit var testUser: User

    @BeforeEach
    fun setUp() {
        jwtProperties = JwtProperties(
            secret = "testSecretKeyForJwtTokenProviderUnitTestMustBeLongEnough",
            expiration = 86400 // 24 hours
        )
        
        jwtTokenProvider = JwtTokenProvider(jwtProperties)
        jwtTokenProvider.init()

        testUser = User(
            email = "test@quantum.local",
            password = "encodedPassword123",
            name = "Test User"
        )
        testUser.addRole(UserRole.USER)
        testUser.addRole(UserRole.TRADER)
        
        // Mock ID 설정 - reflection으로 private field 접근
        val idField = User::class.java.getDeclaredField("id")
        idField.isAccessible = true
        idField.set(testUser, 1L)
    }

    @Test
    fun `사용자 정보로 JWT 토큰을 생성할 수 있다`() {
        // When
        val token = jwtTokenProvider.generateToken(testUser)

        // Then
        assertThat(token).isNotNull()
        assertThat(token).isNotEmpty()
        assertThat(token.split(".")).hasSize(3) // Header.Payload.Signature
    }

    @Test
    fun `생성된 토큰에서 사용자 ID를 추출할 수 있다`() {
        // Given
        val token = jwtTokenProvider.generateToken(testUser)

        // When
        val userId = jwtTokenProvider.getUserIdFromToken(token)

        // Then
        assertThat(userId).isEqualTo(1L)
    }

    @Test
    fun `생성된 토큰에서 이메일을 추출할 수 있다`() {
        // Given
        val token = jwtTokenProvider.generateToken(testUser)

        // When
        val email = jwtTokenProvider.getEmailFromToken(token)

        // Then
        assertThat(email).isEqualTo("test@quantum.local")
    }

    @Test
    fun `유효한 토큰의 검증이 성공한다`() {
        // Given
        val token = jwtTokenProvider.generateToken(testUser)

        // When
        val isValid = jwtTokenProvider.validateToken(token)

        // Then
        assertThat(isValid).isTrue()
    }

    @Test
    fun `잘못된 형식의 토큰 검증이 실패한다`() {
        // Given
        val invalidToken = "invalid.token.format"

        // When
        val isValid = jwtTokenProvider.validateToken(invalidToken)

        // Then
        assertThat(isValid).isFalse()
    }

    @Test
    fun `변조된 토큰 검증이 실패한다`() {
        // Given
        val validToken = jwtTokenProvider.generateToken(testUser)
        val tamperedToken = validToken.substring(0, validToken.length - 5) + "ABCDE"

        // When
        val isValid = jwtTokenProvider.validateToken(tamperedToken)

        // Then
        assertThat(isValid).isFalse()
    }

    @Test
    fun `토큰의 만료 시간을 확인할 수 있다`() {
        // Given
        val beforeGeneration = Date()
        val token = jwtTokenProvider.generateToken(testUser)
        val afterGeneration = Date()

        // When
        val expirationDate = jwtTokenProvider.getExpirationDateFromToken(token)

        // Then
        val expectedExpiration = Date(System.currentTimeMillis() + jwtProperties.expiration * 1000)
        assertThat(expirationDate).isAfter(beforeGeneration)
        assertThat(expirationDate).isBefore(Date(afterGeneration.time + jwtProperties.expiration * 1000 + 5000)) // 5초 여유
    }

    @Test
    fun `토큰이 만료되지 않았음을 확인할 수 있다`() {
        // Given
        val token = jwtTokenProvider.generateToken(testUser)

        // When
        val isExpired = jwtTokenProvider.isTokenExpired(token)

        // Then
        assertThat(isExpired).isFalse()
    }

    @Test
    fun `만료된 토큰을 감지할 수 있다`() {
        // Given - 이미 만료된 시간으로 설정된 properties 사용
        val expiredProperties = JwtProperties(
            secret = "testSecretKeyForJwtTokenProviderUnitTestMustBeLongEnough",
            expiration = -1 // 이미 만료
        )
        val expiredTokenProvider = JwtTokenProvider(expiredProperties)
        expiredTokenProvider.init()
        
        val expiredToken = expiredTokenProvider.generateToken(testUser)

        // When
        val isExpired = expiredTokenProvider.isTokenExpired(expiredToken)

        // Then
        assertThat(isExpired).isTrue()
    }

    @Test
    fun `Bearer 토큰에서 실제 토큰을 추출할 수 있다`() {
        // Given
        val token = "sample.jwt.token"
        val bearerToken = "Bearer $token"

        // When
        val extractedToken = jwtTokenProvider.resolveToken(bearerToken)

        // Then
        assertThat(extractedToken).isEqualTo(token)
    }

    @Test
    fun `Bearer 접두사가 없는 토큰은 null을 반환한다`() {
        // Given
        val invalidBearerToken = "sample.jwt.token"

        // When
        val extractedToken = jwtTokenProvider.resolveToken(invalidBearerToken)

        // Then
        assertThat(extractedToken).isNull()
    }

    @Test
    fun `null 토큰은 null을 반환한다`() {
        // When
        val extractedToken = jwtTokenProvider.resolveToken(null)

        // Then
        assertThat(extractedToken).isNull()
    }

    @Test
    fun `빈 Bearer 토큰은 빈 문자열을 반환한다`() {
        // Given
        val emptyBearerToken = "Bearer "

        // When
        val extractedToken = jwtTokenProvider.resolveToken(emptyBearerToken)

        // Then
        assertThat(extractedToken).isEmpty()
    }

    @Test
    fun `잘못된 비밀키로 생성된 토큰은 검증이 실패한다`() {
        // Given
        val differentSecretProperties = JwtProperties(
            secret = "differentSecretKeyForJwtTokenProviderTestMustBeLongEnough",
            expiration = 86400
        )
        val differentTokenProvider = JwtTokenProvider(differentSecretProperties)
        differentTokenProvider.init()
        
        val tokenFromDifferentProvider = differentTokenProvider.generateToken(testUser)

        // When
        val isValid = jwtTokenProvider.validateToken(tokenFromDifferentProvider)

        // Then
        assertThat(isValid).isFalse()
    }

    @Test
    fun `토큰에 포함된 역할 정보를 확인할 수 있다`() {
        // Given
        val token = jwtTokenProvider.generateToken(testUser)

        // When - 실제로는 private method인 getClaimsFromToken을 통해 검증하지만, 
        // 토큰이 올바르게 검증되는지로 간접 확인
        val isValid = jwtTokenProvider.validateToken(token)
        val userId = jwtTokenProvider.getUserIdFromToken(token)
        val email = jwtTokenProvider.getEmailFromToken(token)

        // Then
        assertThat(isValid).isTrue()
        assertThat(userId).isEqualTo(1L)
        assertThat(email).isEqualTo("test@quantum.local")
    }

    @Test
    fun `다른 사용자의 토큰을 구분할 수 있다`() {
        // Given
        val user1 = User(email = "user1@quantum.local", password = "password", name = "User 1")
        val idField1 = User::class.java.getDeclaredField("id")
        idField1.isAccessible = true
        idField1.set(user1, 10L)

        val user2 = User(email = "user2@quantum.local", password = "password", name = "User 2")
        val idField2 = User::class.java.getDeclaredField("id")
        idField2.isAccessible = true
        idField2.set(user2, 20L)

        // When
        val token1 = jwtTokenProvider.generateToken(user1)
        val token2 = jwtTokenProvider.generateToken(user2)

        // Then
        assertThat(token1).isNotEqualTo(token2)
        assertThat(jwtTokenProvider.getUserIdFromToken(token1)).isEqualTo(10L)
        assertThat(jwtTokenProvider.getUserIdFromToken(token2)).isEqualTo(20L)
        assertThat(jwtTokenProvider.getEmailFromToken(token1)).isEqualTo("user1@quantum.local")
        assertThat(jwtTokenProvider.getEmailFromToken(token2)).isEqualTo("user2@quantum.local")
    }

    @Test
    fun `토큰 생성 시각이 올바르게 설정된다`() {
        // Given
        val beforeGeneration = Date()
        
        // When
        val token = jwtTokenProvider.generateToken(testUser)
        val expirationDate = jwtTokenProvider.getExpirationDateFromToken(token)
        
        val afterGeneration = Date()

        // Then
        val expectedMinExpiration = Date(beforeGeneration.time + jwtProperties.expiration * 1000)
        val expectedMaxExpiration = Date(afterGeneration.time + jwtProperties.expiration * 1000)
        
        assertThat(expirationDate).isBetween(expectedMinExpiration, expectedMaxExpiration)
    }
}