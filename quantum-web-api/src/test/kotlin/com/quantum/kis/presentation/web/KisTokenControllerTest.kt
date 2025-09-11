package com.quantum.kis.presentation.web

import com.quantum.kis.application.usecase.KisTokenUseCase
import com.quantum.kis.domain.KisEnvironment
import com.quantum.kis.infrastructure.client.KisTokenResponse
import com.fasterxml.jackson.databind.ObjectMapper
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.mockito.BDDMockito.given
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest
import org.springframework.boot.test.mock.mockito.MockBean
import org.springframework.http.MediaType
import org.springframework.test.context.ActiveProfiles
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.*
import java.time.LocalDateTime

@WebMvcTest(KisTokenController::class)
@ActiveProfiles("test")
@DisplayName("KisTokenController 단위 테스트")
class KisTokenControllerTest {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @Autowired
    private lateinit var objectMapper: ObjectMapper

    @MockBean
    private lateinit var kisTokenUseCase: KisTokenUseCase

    @Test
    fun `KIS 토큰 갱신 요청이 성공한다`() {
        // Given
        val mockTokenResponse = KisTokenResponse(
            access_token = "test-access-token",
            token_type = "Bearer",
            expires_in = 21600,
            issuedAt = LocalDateTime.now(),
            environment = KisEnvironment.SANDBOX
        )
        given(kisTokenUseCase.refreshToken(KisEnvironment.SANDBOX)).willReturn(mockTokenResponse)

        // When & Then
        mockMvc.perform(post("/api/v1/kis/token/refresh")
            .param("environment", "SANDBOX")
            .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON))
            .andExpect(jsonPath("$.access_token").value("test-access-token"))
            .andExpect(jsonPath("$.token_type").value("Bearer"))
            .andExpect(jsonPath("$.expires_in").value(21600))
    }

    @Test
    fun `환경 파라미터 없이 요청하면 기본값이 적용된다`() {
        // Given
        val mockTokenResponse = KisTokenResponse(
            access_token = "test-token",
            environment = KisEnvironment.SANDBOX
        )
        given(kisTokenUseCase.refreshToken(KisEnvironment.SANDBOX)).willReturn(mockTokenResponse)

        // When & Then
        mockMvc.perform(post("/api/v1/kis/token/refresh")
            .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.access_token").value("test-token"))
    }

    @Test
    fun `LIVE 환경 토큰 요청이 가능하다`() {
        // Given
        val mockTokenResponse = KisTokenResponse(
            access_token = "live-token",
            environment = KisEnvironment.LIVE
        )
        given(kisTokenUseCase.refreshToken(KisEnvironment.LIVE)).willReturn(mockTokenResponse)

        // When & Then
        mockMvc.perform(post("/api/v1/kis/token/refresh")
            .param("environment", "LIVE")
            .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.access_token").value("live-token"))
    }
}