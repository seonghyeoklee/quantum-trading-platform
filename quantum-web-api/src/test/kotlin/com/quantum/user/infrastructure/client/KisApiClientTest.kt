package com.quantum.user.infrastructure.client

import com.quantum.user.infrastructure.dto.KisTokenResponse
import com.quantum.user.infrastructure.dto.KisErrorResponse
import com.fasterxml.jackson.databind.ObjectMapper
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.http.HttpMethod
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.test.context.ActiveProfiles
import org.springframework.test.web.client.MockRestServiceServer
import org.springframework.test.web.client.match.MockRestRequestMatchers.*
import org.springframework.test.web.client.response.MockRestResponseCreators.*
import org.springframework.web.client.RestTemplate
import org.springframework.web.client.HttpClientErrorException

@SpringBootTest
@ActiveProfiles("test")
@DisplayName("KisApiClient 단위 테스트")
class KisApiClientTest {

    @Autowired
    private lateinit var kisApiClient: KisApiClient

    @Autowired
    private lateinit var restTemplate: RestTemplate

    @Autowired
    private lateinit var objectMapper: ObjectMapper

    private lateinit var mockServer: MockRestServiceServer

    @BeforeEach
    fun setUp() {
        mockServer = MockRestServiceServer.createServer(restTemplate)
    }

    @Test
    fun `KIS 토큰을 성공적으로 발급받을 수 있다`() {
        // Given
        val expectedResponse = KisTokenResponse(
            accessToken = "test-access-token",
            tokenType = "Bearer",
            expiresIn = 86400,
            accessTokenTokenExpired = "2024-01-02 09:00:00"
        )

        mockServer.expect(requestTo("https://openapivts.koreainvestment.com:29443/oauth2/tokenP"))
            .andExpect(method(HttpMethod.POST))
            .andExpected(header("Content-Type", "application/json"))
            .andExpect(jsonPath("$.grant_type").value("client_credentials"))
            .andExpected(jsonPath("$.appkey").exists())
            .andExpected(jsonPath("$.appsecret").exists())
            .andRespond(
                withSuccess(
                    objectMapper.writeValueAsString(expectedResponse),
                    MediaType.APPLICATION_JSON
                )
            )

        // When
        val result = kisApiClient.getToken()

        // Then
        assertThat(result).isNotNull()
        assertThat(result.accessToken).isEqualTo("test-access-token")
        assertThat(result.tokenType).isEqualTo("Bearer")
        assertThat(result.expiresIn).isEqualTo(86400)
        mockServer.verify()
    }

    @Test
    fun `KIS 토큰 발급 실패 시 예외가 발생한다`() {
        // Given
        val errorResponse = KisErrorResponse(
            rtCd = "1",
            msgCd = "EGW00123",
            msg1 = "Invalid appkey or appsecret"
        )

        mockServer.expect(requestTo("https://openapivts.koreainvestment.com:29443/oauth2/tokenP"))
            .andExpect(method(HttpMethod.POST))
            .andRespond(
                withStatus(HttpStatus.BAD_REQUEST)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(objectMapper.writeValueAsString(errorResponse))
            )

        // When & Then
        assertThrows<HttpClientErrorException> {
            kisApiClient.getToken()
        }
        mockServer.verify()
    }

    @Test
    fun `토큰 갱신 요청을 올바르게 처리한다`() {
        // Given
        val expectedResponse = KisTokenResponse(
            accessToken = "refreshed-access-token",
            tokenType = "Bearer",
            expiresIn = 86400,
            accessTokenTokenExpired = "2024-01-03 09:00:00"
        )

        mockServer.expect(requestTo("https://openapivts.koreainvestment.com:29443/oauth2/tokenP"))
            .andExpect(method(HttpMethod.POST))
            .andExpected(header("Content-Type", "application/json"))
            .andRespond(
                withSuccess(
                    objectMapper.writeValueAsString(expectedResponse),
                    MediaType.APPLICATION_JSON
                )
            )

        // When
        val result = kisApiClient.refreshToken()

        // Then
        assertThat(result).isNotNull()
        assertThat(result.accessToken).isEqualTo("refreshed-access-token")
        assertThat(result.expiresIn).isEqualTo(86400)
        mockServer.verify()
    }

    @Test
    fun `국내 주식 가격 조회 API 호출이 올바르게 수행된다`() {
        // Given
        val stockCode = "005930"
        val mockResponse = """
        {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "stck_prpr": "75000",
                "prdy_vrss": "1000",
                "prdy_vrss_sign": "2",
                "prdy_ctrt": "1.35"
            }
        }
        """.trimIndent()

        mockServer.expect(requestTo(startsWith("https://openapivts.koreainvestment.com:29443/uapi/domestic-stock/v1/quotations/inquire-price")))
            .andExpect(method(HttpMethod.GET))
            .andExpected(header("Authorization", "Bearer test-token"))
            .andExpected(header("appkey", "test-appkey"))
            .andExpected(header("appsecret", "test-appsecret"))
            .andExpected(header("tr_id", "FHKST01010100"))
            .andExpectedqueryParam("fid_cond_mrkt_div_code", "J")
            .andExpectedqueryParam("fid_input_iscd", stockCode)
            .andRespond(
                withSuccess(mockResponse, MediaType.APPLICATION_JSON)
            )

        // When
        val result = kisApiClient.getDomesticStockPrice(stockCode, "test-token")

        // Then
        assertThat(result).isNotNull()
        assertThat(result.contains("75000")).isTrue()
        mockServer.verify()
    }

    @Test
    fun `잘못된 종목코드로 주식 가격 조회 시 에러 응답을 처리한다`() {
        // Given
        val invalidStockCode = "999999"
        val errorResponse = """
        {
            "rt_cd": "1",
            "msg_cd": "EGW00116",
            "msg1": "조회할 수 없는 종목입니다."
        }
        """.trimIndent()

        mockServer.expect(requestTo(startsWith("https://openapivts.koreainvestment.com:29443/uapi/domestic-stock/v1/quotations/inquire-price")))
            .andExpect(method(HttpMethod.GET))
            .andRespond(
                withStatus(HttpStatus.BAD_REQUEST)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(errorResponse)
            )

        // When & Then
        assertThrows<HttpClientErrorException> {
            kisApiClient.getDomesticStockPrice(invalidStockCode, "test-token")
        }
        mockServer.verify()
    }

    @Test
    fun `네트워크 오류 시 적절한 예외 처리가 된다`() {
        // Given
        val stockCode = "005930"

        mockServer.expect(requestTo(startsWith("https://openapivts.koreainvestment.com:29443/uapi/domestic-stock/v1/quotations/inquire-price")))
            .andExpect(method(HttpMethod.GET))
            .andRespond(withServerError())

        // When & Then
        assertThrows<Exception> {
            kisApiClient.getDomesticStockPrice(stockCode, "test-token")
        }
        mockServer.verify()
    }

    @Test
    fun `요청 헤더가 올바르게 설정되는지 확인한다`() {
        // Given
        val token = "test-access-token"
        val mockResponse = """
        {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "output": {"stck_prpr": "75000"}
        }
        """.trimIndent()

        mockServer.expect(requestTo(anyOf()))
            .andExpect(method(HttpMethod.GET))
            .andExpected(header("Authorization", "Bearer $token"))
            .andExpected(header("Content-Type", "application/json; charset=utf-8"))
            .andExpected(header("appkey"))
            .andExpected(header("appsecret"))
            .andExpected(header("tr_id"))
            .andRespond(withSuccess(mockResponse, MediaType.APPLICATION_JSON))

        // When
        kisApiClient.getDomesticStockPrice("005930", token)

        // Then
        mockServer.verify()
    }

    @Test
    fun `API 응답 파싱이 올바르게 수행되는지 확인한다`() {
        // Given
        val complexResponse = """
        {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "stck_shrn_iscd": "005930",
                "stck_prpr": "75000",
                "prdy_vrss": "1000",
                "prdy_vrss_sign": "2",
                "prdy_ctrt": "1.35",
                "acml_vol": "12345678",
                "acml_tr_pbmn": "987654321000",
                "hts_kor_isnm": "삼성전자",
                "stck_mxpr": "77000",
                "stck_llam": "74000"
            }
        }
        """.trimIndent()

        mockServer.expect(requestTo(anyOf()))
            .andExpect(method(HttpMethod.GET))
            .andRespond(withSuccess(complexResponse, MediaType.APPLICATION_JSON))

        // When
        val result = kisApiClient.getDomesticStockPrice("005930", "test-token")

        // Then
        assertThat(result).contains("005930")
        assertThat(result).contains("75000")
        assertThat(result).contains("삼성전자")
        assertThat(result).contains("77000") // 최고가
        assertThat(result).contains("74000") // 최저가
        mockServer.verify()
    }
}