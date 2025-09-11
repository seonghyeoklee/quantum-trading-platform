package com.quantum.stock.presentation.web

import com.quantum.stock.domain.DomesticMarketType
import com.quantum.stock.domain.DomesticStock
import com.quantum.stock.infrastructure.persistence.DomesticStockRepository
import com.fasterxml.jackson.databind.ObjectMapper
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.mockito.BDDMockito.given
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest
import org.springframework.boot.test.mock.mockito.MockBean
import org.springframework.data.domain.*
import org.springframework.http.MediaType
import org.springframework.test.context.ActiveProfiles
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.*
import java.time.LocalDate

@WebMvcTest(DomesticStockController::class)
@ActiveProfiles("test")
@DisplayName("DomesticStockController 단위 테스트")
class DomesticStockControllerTest {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @Autowired
    private lateinit var objectMapper: ObjectMapper

    @MockBean
    private lateinit var domesticStockRepository: DomesticStockRepository

    private lateinit var sampleStocks: List<DomesticStock>

    @BeforeEach
    fun setUp() {
        sampleStocks = listOf(
            DomesticStock.createKospi(
                stockCode = "005930",
                stockName = "삼성전자",
                listingDate = LocalDate.of(1975, 6, 11),
                sectorCode = "IT"
            ),
            DomesticStock.createKosdaq(
                stockCode = "035720",
                stockName = "카카오",
                listingDate = LocalDate.of(2017, 7, 10),
                sectorCode = "IT"
            )
        )
    }

    @Test
    fun `국내주식 전체 목록을 조회할 수 있다`() {
        // Given
        val pageable = PageRequest.of(0, 20, Sort.by("stockCode").ascending())
        val stockPage = PageImpl(sampleStocks, pageable, 2)
        given(domesticStockRepository.findByIsActiveTrue(pageable)).willReturn(stockPage)

        // When & Then
        mockMvc.perform(get("/api/v1/stocks/domestic")
            .param("page", "0")
            .param("size", "20"))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON))
            .andExpect(jsonPath("$.stocks").isArray())
            .andExpect(jsonPath("$.stocks.length()").value(2))
            .andExpect(jsonPath("$.totalElements").value(2))
            .andExpect(jsonPath("$.totalPages").value(1))
    }

    @Test
    fun `시장별 종목을 조회할 수 있다`() {
        // Given
        val kospiStocks = listOf(sampleStocks[0])
        val pageable = PageRequest.of(0, 20, Sort.by("stockCode").ascending())
        val stockPage = PageImpl(kospiStocks, pageable, 1)
        given(domesticStockRepository.findByMarketTypeAndIsActiveTrue(DomesticMarketType.KOSPI, pageable))
            .willReturn(stockPage)

        // When & Then
        mockMvc.perform(get("/api/v1/stocks/domestic")
            .param("marketType", "KOSPI"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.stocks.length()").value(1))
            .andExpect(jsonPath("$.stocks[0].stockCode").value("005930"))
            .andExpect(jsonPath("$.stocks[0].marketType").value("KOSPI"))
    }

    @Test
    fun `페이지 크기가 100을 초과하면 100으로 제한된다`() {
        // Given
        val pageable = PageRequest.of(0, 100, Sort.by("stockCode").ascending())
        val stockPage = PageImpl(emptyList<DomesticStock>(), pageable, 0)
        given(domesticStockRepository.findByIsActiveTrue(pageable)).willReturn(stockPage)

        // When & Then
        mockMvc.perform(get("/api/v1/stocks/domestic")
            .param("size", "150"))
            .andExpect(status().isOk())
    }

    @Test
    fun `잘못된 페이지 번호로 요청하면 기본값이 적용된다`() {
        // Given
        val pageable = PageRequest.of(0, 20, Sort.by("stockCode").ascending())
        val stockPage = PageImpl(emptyList<DomesticStock>(), pageable, 0)
        given(domesticStockRepository.findByIsActiveTrue(pageable)).willReturn(stockPage)

        // When & Then
        mockMvc.perform(get("/api/v1/stocks/domestic"))
            .andExpect(status().isOk())
    }
}