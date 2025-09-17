package com.quantum.kis.presentation.web

import com.quantum.kis.application.service.KisTokenService
import com.quantum.kis.domain.KisEnvironment
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest
import org.springframework.boot.test.mock.mockito.MockBean
import org.springframework.test.context.ActiveProfiles
import org.springframework.test.web.servlet.MockMvc
import org.assertj.core.api.Assertions.*

@WebMvcTest(KisTokenController::class)
@ActiveProfiles("test")
@DisplayName("KisTokenController 단위 테스트")
class KisTokenControllerTest {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @MockBean
    private lateinit var kisTokenService: KisTokenService

    @Test
    fun `컨트롤러가 올바르게 로드된다`() {
        // Given & When & Then
        assertThat(mockMvc).isNotNull()
        assertThat(kisTokenService).isNotNull()
    }

    @Test
    fun `KisEnvironment enum이 올바르게 정의되어 있다`() {
        // Given & When & Then
        assertThat(KisEnvironment.SANDBOX).isNotNull()
        assertThat(KisEnvironment.LIVE).isNotNull()
        assertThat(KisEnvironment.values()).hasSize(2)
    }
}