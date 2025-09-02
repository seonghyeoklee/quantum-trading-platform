package com.quantum.kis.integration

import com.fasterxml.jackson.databind.ObjectMapper
import com.quantum.kis.application.service.KisAccountRequest
import com.quantum.kis.domain.KisEnvironment
import com.quantum.kis.presentation.dto.ApiResponse
import com.quantum.kis.presentation.web.*
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureWebMvc
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.http.MediaType
import org.springframework.security.test.context.support.WithMockUser
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.*
import org.springframework.transaction.annotation.Transactional

/**
 * KIS 토큰 관리 시스템 통합 테스트
 * 
 * MVP 1.0 Hybrid KIS Token Architecture Phase 1 검증
 */
@SpringBootTest
@AutoConfigureWebMvc
@Transactional
@DisplayName("KIS 토큰 관리 시스템 통합 테스트")
class KisTokenIntegrationTest {

    @Autowired
    private lateinit var mockMvc: MockMvc
    
    @Autowired
    private lateinit var objectMapper: ObjectMapper

    @Test
    @WithMockUser(username = "1")
    @DisplayName("KIS 계정 검증 API 테스트")
    fun testAccountValidation() {
        // Given: 테스트용 KIS 계정 검증 요청
        val request = KisAccountValidationRequest(
            appKey = "test-app-key",
            appSecret = "test-app-secret", 
            accountNumber = "12345678-01",
            environment = KisEnvironment.SANDBOX,
            accountAlias = "테스트 계정"
        )

        // When: 계정 검증 API 호출
        mockMvc.perform(
            post("/api/v1/kis/account/validate")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request))
        )
        // Then: 계정 검증 응답 확인 (실제 KIS API 없으므로 에러 응답 예상)
        .andExpect(status().isBadRequest)
        .andExpect(jsonPath("$.success").value(false))
        .andExpect(jsonPath("$.error").exists())
    }

    @Test
    @WithMockUser(username = "1")
    @DisplayName("KIS 토큰 발급 API 테스트")
    fun testTokenIssuance() {
        // Given: 테스트용 KIS 토큰 발급 요청
        val request = KisTokenIssueRequest(
            appKey = "test-app-key",
            appSecret = "test-app-secret",
            accountNumber = "12345678-01", 
            environment = KisEnvironment.SANDBOX,
            accountAlias = "테스트 계정"
        )

        // When: 토큰 발급 API 호출
        mockMvc.perform(
            post("/api/v1/kis/token")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request))
        )
        // Then: 토큰 발급 응답 확인 (실제 KIS API 없으므로 에러 응답 예상)
        .andExpect(status().isInternalServerError)
        .andExpect(jsonPath("$.success").value(false))
        .andExpect(jsonPath("$.error").exists())
    }

    @Test
    @WithMockUser(username = "1") 
    @DisplayName("KIS 토큰 갱신 API 테스트")
    fun testTokenRefresh() {
        // Given: 테스트용 KIS 토큰 갱신 요청
        val request = KisTokenRefreshRequest(
            environment = KisEnvironment.SANDBOX
        )

        // When: 토큰 갱신 API 호출
        mockMvc.perform(
            post("/api/v1/kis/token/refresh")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request))
        )
        // Then: 토큰 갱신 응답 확인 (계정 없으므로 에러 응답 예상)
        .andExpect(status().isUnauthorized)
        .andExpect(jsonPath("$.success").value(false))
        .andExpect(jsonPath("$.error").exists())
    }

    @Test
    @WithMockUser(username = "1")
    @DisplayName("현재 토큰 조회 API 테스트")
    fun testCurrentTokenRetrieval() {
        // When: 현재 토큰 조회 API 호출
        mockMvc.perform(
            get("/api/v1/kis/token/current")
                .param("environment", "SANDBOX")
        )
        // Then: 토큰 조회 응답 확인 (토큰 없으므로 null 응답 예상)
        .andExpect(status().isOk)
        .andExpect(jsonPath("$.success").value(true))
        .andExpect(jsonPath("$.data").doesNotExist())
    }

    @Test
    @WithMockUser(username = "1")
    @DisplayName("토큰 상태 확인 API 테스트")
    fun testTokenStatus() {
        // When: 토큰 상태 확인 API 호출
        mockMvc.perform(
            get("/api/v1/kis/token/status")
                .param("environment", "SANDBOX")
        )
        // Then: 토큰 상태 응답 확인
        .andExpect(status().isOk)
        .andExpect(jsonPath("$.success").value(true))
        .andExpect(jsonPath("$.data.hasToken").value(false))
        .andExpect(jsonPath("$.data.isValid").value(false))
        .andExpect(jsonPath("$.data.status").value("토큰 없음"))
        .andExpect(jsonPath("$.data.environment").value("SANDBOX"))
    }

    @Test
    @WithMockUser(username = "1")
    @DisplayName("전체 토큰 관리 워크플로우 테스트")
    fun testCompleteTokenManagementWorkflow() {
        // 1. 토큰 상태 확인 - 초기 상태
        mockMvc.perform(
            get("/api/v1/kis/token/status")
                .param("environment", "SANDBOX")
        )
        .andExpect(status().isOk)
        .andExpect(jsonPath("$.data.hasToken").value(false))

        // 2. 계정 검증 시도
        val validationRequest = KisAccountValidationRequest(
            appKey = "test-app-key",
            appSecret = "test-app-secret",
            accountNumber = "12345678-01",
            environment = KisEnvironment.SANDBOX
        )
        
        mockMvc.perform(
            post("/api/v1/kis/account/validate")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validationRequest))
        )
        .andExpect(status().isBadRequest) // KIS API 없으므로 실패 예상

        // 3. 토큰 발급 시도
        val tokenRequest = KisTokenIssueRequest(
            appKey = "test-app-key",
            appSecret = "test-app-secret", 
            accountNumber = "12345678-01",
            environment = KisEnvironment.SANDBOX
        )
        
        mockMvc.perform(
            post("/api/v1/kis/token")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(tokenRequest))
        )
        .andExpect(status().isInternalServerError) // KIS API 없으므로 실패 예상

        // 4. 현재 토큰 조회 - 여전히 토큰 없음
        mockMvc.perform(
            get("/api/v1/kis/token/current")
                .param("environment", "SANDBOX")
        )
        .andExpect(status().isOk)
        .andExpect(jsonPath("$.data").doesNotExist())
    }

    @Test
    @DisplayName("인증 없이 토큰 API 접근 테스트")
    fun testTokenApiWithoutAuthentication() {
        // When: 인증 없이 토큰 상태 확인 시도
        mockMvc.perform(
            get("/api/v1/kis/token/status")
                .param("environment", "SANDBOX")
        )
        // Then: 인증 오류 응답 확인
        .andExpect(status().isUnauthorized)
    }

    @Test
    @WithMockUser(username = "1")
    @DisplayName("잘못된 환경 파라미터로 API 호출 테스트")  
    fun testTokenApiWithInvalidEnvironment() {
        // When: 잘못된 환경 파라미터로 토큰 상태 확인
        mockMvc.perform(
            get("/api/v1/kis/token/status")
                .param("environment", "INVALID_ENV")
        )
        // Then: 파라미터 오류 응답 확인
        .andExpect(status().isBadRequest)
    }
}