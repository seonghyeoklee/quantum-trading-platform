package com.quantum.user.presentation.web

import com.fasterxml.jackson.databind.ObjectMapper
import com.quantum.user.application.port.outgoing.UserRepository
import com.quantum.user.domain.User
import com.quantum.user.domain.UserRole
import com.quantum.user.domain.UserStatus
import com.quantum.user.presentation.dto.LoginRequest
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.http.MediaType
import org.springframework.security.crypto.password.PasswordEncoder
import org.springframework.test.context.ActiveProfiles
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.*
import org.springframework.transaction.annotation.Transactional

/**
 * AuthController 통합 테스트
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class AuthControllerIntegrationTest {
    
    @Autowired
    private lateinit var mockMvc: MockMvc
    
    @Autowired
    private lateinit var objectMapper: ObjectMapper
    
    @Autowired
    private lateinit var userRepository: UserRepository
    
    @Autowired
    private lateinit var passwordEncoder: PasswordEncoder
    
    @BeforeEach
    fun setUp() {
        // Create admin user for testing
        if (userRepository.findByEmail("admin@quantum.local").isEmpty) {
            val admin = User(
                email = "admin@quantum.local",
                name = "Quantum Admin",
                password = passwordEncoder.encode("admin123"),
                status = UserStatus.ACTIVE
            )
            admin.addRole(UserRole.ADMIN)
            admin.addRole(UserRole.TRADER)
            
            userRepository.save(admin)
        }
    }
    
    @Test
    fun `로그인 성공 테스트`() {
        // Given
        val loginRequest = LoginRequest(
            email = "admin@quantum.local", 
            password = "admin123"
        )
        
        // When & Then
        mockMvc.perform(
            post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest))
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.accessToken").exists())
            .andExpect(jsonPath("$.expiresIn").value(86400))
            .andExpect(jsonPath("$.user.email").value("admin@quantum.local"))
            .andExpect(jsonPath("$.user.name").value("Quantum Admin"))
            .andExpect(jsonPath("$.user.roles").isArray)
    }
    
    @Test
    fun `로그인 실패 테스트 - 잘못된 비밀번호`() {
        // Given
        val loginRequest = LoginRequest(
            email = "admin@quantum.local",
            password = "wrongpassword"
        )
        
        // When & Then
        mockMvc.perform(
            post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest))
        )
            .andExpect(status().isUnauthorized)
            .andExpect(jsonPath("$.error").value("AUTHENTICATION_FAILED"))
            .andExpect(jsonPath("$.message").exists())
    }
    
    @Test
    fun `로그인 실패 테스트 - 존재하지 않는 사용자`() {
        // Given
        val loginRequest = LoginRequest(
            email = "nonexistent@quantum.local",
            password = "password123"
        )
        
        // When & Then
        mockMvc.perform(
            post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest))
        )
            .andExpect(status().isUnauthorized)
            .andExpect(jsonPath("$.error").value("AUTHENTICATION_FAILED"))
    }
    
    @Test
    fun `로그인 유효성 검사 실패 테스트 - 빈 이메일`() {
        // Given
        val loginRequest = LoginRequest(
            email = "",
            password = "password123"
        )
        
        // When & Then
        mockMvc.perform(
            post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest))
        )
            .andExpect(status().isBadRequest)
            .andExpect(jsonPath("$.error").value("VALIDATION_ERROR"))
    }
    
    @Test
    fun `로그인 유효성 검사 실패 테스트 - 잘못된 이메일 형식`() {
        // Given
        val loginRequest = LoginRequest(
            email = "invalid-email",
            password = "password123"
        )
        
        // When & Then
        mockMvc.perform(
            post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest))
        )
            .andExpect(status().isBadRequest)
            .andExpect(jsonPath("$.error").value("VALIDATION_ERROR"))
    }
    
    @Test
    fun `인증 없이 보호된 리소스 접근 테스트`() {
        // When & Then
        mockMvc.perform(get("/api/v1/auth/me"))
            .andExpect(status().isForbidden)
    }
    
    private fun getAuthToken(): String {
        val loginRequest = LoginRequest(
            email = "admin@quantum.local",
            password = "admin123"
        )
        
        val result = mockMvc.perform(
            post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest))
        ).andReturn()
        
        val content = result.response.contentAsString
        val response = objectMapper.readTree(content)
        return response.get("accessToken").asText()
    }
    
    @Test
    fun `현재 사용자 정보 조회 테스트`() {
        // Given
        val token = getAuthToken()
        
        // When & Then
        mockMvc.perform(
            get("/api/v1/auth/me")
                .header("Authorization", "Bearer $token")
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.email").value("admin@quantum.local"))
            .andExpect(jsonPath("$.name").value("Quantum Admin"))
            .andExpect(jsonPath("$.roles").isArray)
    }
    
    @Test
    fun `로그아웃 테스트`() {
        // Given
        val token = getAuthToken()
        
        // When & Then
        mockMvc.perform(
            post("/api/v1/auth/logout")
                .header("Authorization", "Bearer $token")
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.message").value("로그아웃 완료"))
    }
}