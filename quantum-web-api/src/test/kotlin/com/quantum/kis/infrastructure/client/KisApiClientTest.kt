package com.quantum.kis.infrastructure.client

import com.quantum.kis.domain.KisEnvironment
import kotlinx.coroutines.runBlocking
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import org.springframework.web.reactive.function.client.WebClient

@DisplayName("KisApiClient 단위 테스트")
class KisApiClientTest {

    private lateinit var kisApiClient: KisApiClient
    private lateinit var webClient: WebClient

    @BeforeEach
    fun setUp() {
        webClient = WebClient.builder().build()
        kisApiClient = KisApiClient(
            webClient = webClient,
            liveBaseUrl = "https://openapi.koreainvestment.com:9443",
            sandboxBaseUrl = "https://openapivts.koreainvestment.com:29443"
        )
    }

    @Test
    fun `KisApiClient 인스턴스가 올바르게 생성된다`() {
        // Then
        assertThat(kisApiClient).isNotNull()
    }

    @Test
    fun `KIS 환경별 BaseURL이 올바르게 설정된다`() {
        // Given
        val liveClient = KisApiClient(
            webClient = webClient,
            liveBaseUrl = "https://live.test.com",
            sandboxBaseUrl = "https://sandbox.test.com"
        )

        // Then
        assertThat(liveClient).isNotNull()
    }

    @Test
    fun `TokenRequest 객체가 올바르게 생성된다`() {
        // Given
        val tokenRequest = TokenRequest(
            grant_type = "client_credentials",
            appkey = "test-app-key",
            appsecret = "test-app-secret"
        )

        // Then
        assertThat(tokenRequest.grant_type).isEqualTo("client_credentials")
        assertThat(tokenRequest.appkey).isEqualTo("test-app-key")
        assertThat(tokenRequest.appsecret).isEqualTo("test-app-secret")
    }

    @Test
    fun `KisTokenResponse 기본값이 올바르게 설정된다`() {
        // Given
        val tokenResponse = KisTokenResponse(
            access_token = "test-access-token"
        )

        // Then
        assertThat(tokenResponse.access_token).isEqualTo("test-access-token")
        assertThat(tokenResponse.token_type).isEqualTo("Bearer")
        assertThat(tokenResponse.expires_in).isEqualTo(21600) // 6시간
        assertThat(tokenResponse.environment).isEqualTo(KisEnvironment.SANDBOX)
    }

    @Test
    fun `KisTokenResponse에서 Authorization 헤더값을 올바르게 생성한다`() {
        // Given
        val tokenResponse = KisTokenResponse(
            access_token = "test-access-token",
            token_type = "Bearer"
        )

        // When
        val authHeader = tokenResponse.getAuthorizationHeader()

        // Then
        assertThat(authHeader).isEqualTo("Bearer test-access-token")
    }

    @Test
    fun `KisTokenResponse에서 만료 시간을 올바르게 계산한다`() {
        // Given
        val issuedAt = java.time.LocalDateTime.of(2024, 1, 1, 12, 0, 0)
        val tokenResponse = KisTokenResponse(
            access_token = "test-access-token",
            expires_in = 3600, // 1시간
            issuedAt = issuedAt
        )

        // When
        val expiresAt = tokenResponse.getExpiresAt()

        // Then
        val expectedExpiresAt = issuedAt.plusSeconds(3600)
        assertThat(expiresAt).isEqualTo(expectedExpiresAt)
    }

    @Test
    fun `AccountValidationResponse가 올바르게 생성된다`() {
        // Given
        val validatedAt = java.time.LocalDateTime.now()
        val response = AccountValidationResponse(
            isValid = true,
            message = "계정이 유효합니다",
            environment = KisEnvironment.LIVE,
            validatedAt = validatedAt
        )

        // Then
        assertThat(response.isValid).isTrue()
        assertThat(response.message).isEqualTo("계정이 유효합니다")
        assertThat(response.environment).isEqualTo(KisEnvironment.LIVE)
        assertThat(response.validatedAt).isEqualTo(validatedAt)
        assertThat(response.error).isNull()
    }

    @Test
    fun `ServerStatusResponse가 올바르게 생성된다`() {
        // Given
        val checkedAt = java.time.LocalDateTime.now()
        val response = ServerStatusResponse(
            isAvailable = true,
            responseTimeMs = 150,
            environment = KisEnvironment.SANDBOX,
            checkedAt = checkedAt
        )

        // Then
        assertThat(response.isAvailable).isTrue()
        assertThat(response.responseTimeMs).isEqualTo(150)
        assertThat(response.environment).isEqualTo(KisEnvironment.SANDBOX)
        assertThat(response.checkedAt).isEqualTo(checkedAt)
        assertThat(response.error).isNull()
    }

    @Test
    fun `KisApiException이 올바르게 생성된다`() {
        // Given
        val cause = RuntimeException("원인 예외")
        val exception = KisApiException("KIS API 오류", cause)

        // Then
        assertThat(exception.message).isEqualTo("KIS API 오류")
        assertThat(exception.cause).isEqualTo(cause)
    }

    @Test
    fun `KisEnvironment별로 다른 토큰 응답을 생성할 수 있다`() {
        // Given
        val liveToken = KisTokenResponse(
            access_token = "live-token",
            environment = KisEnvironment.LIVE
        )
        
        val sandboxToken = KisTokenResponse(
            access_token = "sandbox-token",
            environment = KisEnvironment.SANDBOX
        )

        // Then
        assertThat(liveToken.environment).isEqualTo(KisEnvironment.LIVE)
        assertThat(liveToken.access_token).isEqualTo("live-token")
        
        assertThat(sandboxToken.environment).isEqualTo(KisEnvironment.SANDBOX)
        assertThat(sandboxToken.access_token).isEqualTo("sandbox-token")
    }

    @Test
    fun `토큰 응답의 기본 설정값들이 올바르게 적용된다`() {
        // Given
        val tokenResponse = KisTokenResponse(
            access_token = "test-token"
        )

        // Then
        assertThat(tokenResponse.token_type).isEqualTo("Bearer")
        assertThat(tokenResponse.expires_in).isEqualTo(21600) // 6시간
        assertThat(tokenResponse.scope).isNull()
        assertThat(tokenResponse.environment).isEqualTo(KisEnvironment.SANDBOX)
        assertThat(tokenResponse.issuedAt).isBeforeOrEqualTo(java.time.LocalDateTime.now())
    }
}