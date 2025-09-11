package com.quantum.stock.infrastructure.persistence

import com.quantum.stock.domain.DomesticMarketType
import com.quantum.stock.domain.DomesticStock
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager
import org.springframework.test.context.ActiveProfiles
import java.time.LocalDate

@DataJpaTest
@ActiveProfiles("test")
@DisplayName("DomesticStockRepository 단위 테스트")
class DomesticStockRepositoryTest {

    @Autowired
    private lateinit var repository: DomesticStockRepository

    @Autowired
    private lateinit var entityManager: TestEntityManager

    private lateinit var samsungStock: DomesticStock
    private lateinit var skHynixStock: DomesticStock
    private lateinit var kakaoStock: DomesticStock

    @BeforeEach
    fun setUp() {
        samsungStock = DomesticStock.createKospi(
            stockCode = "005930",
            stockName = "삼성전자",
            listingDate = LocalDate.of(1975, 6, 11),
            sectorCode = "IT"
        )

        skHynixStock = DomesticStock.createKospi(
            stockCode = "000660",
            stockName = "SK하이닉스",
            listingDate = LocalDate.of(1996, 12, 26),
            sectorCode = "IT"
        )

        kakaoStock = DomesticStock.createKosdaq(
            stockCode = "035720",
            stockName = "카카오",
            listingDate = LocalDate.of(2017, 7, 10),
            sectorCode = "IT"
        )
    }

    @Test
    fun `종목코드로 주식을 조회할 수 있다`() {
        // Given
        entityManager.persistAndFlush(samsungStock)
        entityManager.clear()

        // When
        val found = repository.findByStockCode("005930")

        // Then
        assertThat(found).isNotNull()
        assertThat(found!!.stockCode).isEqualTo("005930")
        assertThat(found.stockName).isEqualTo("삼성전자")
        assertThat(found.marketType).isEqualTo(DomesticMarketType.KOSPI)
    }

    @Test
    fun `존재하지 않는 종목코드로 조회하면 null을 반환한다`() {
        // When
        val found = repository.findByStockCode("999999")

        // Then
        assertThat(found).isNull()
    }

    @Test
    fun `시장 유형별로 활성 주식을 조회할 수 있다`() {
        // Given
        entityManager.persistAndFlush(samsungStock)
        entityManager.persistAndFlush(skHynixStock)
        entityManager.persistAndFlush(kakaoStock)

        // When
        val kospiStocks = repository.findByMarketTypeAndIsActiveTrueOrderByStockCodeAsc(DomesticMarketType.KOSPI)
        val kosdaqStocks = repository.findByMarketTypeAndIsActiveTrueOrderByStockCodeAsc(DomesticMarketType.KOSDAQ)

        // Then
        assertThat(kospiStocks).hasSize(2)
        assertThat(kospiStocks.map { it.stockCode }).containsExactlyInAnyOrder("005930", "000660")

        assertThat(kosdaqStocks).hasSize(1)
        assertThat(kosdaqStocks[0].stockCode).isEqualTo("035720")
    }

    @Test
    fun `종목명으로 검색할 수 있다`() {
        // Given
        entityManager.persistAndFlush(samsungStock)
        entityManager.persistAndFlush(kakaoStock)

        // When
        val samsungResults = repository.findByStockNameContainingAndIsActiveTrueOrderByStockNameAsc("삼성")
        val kakaoResults = repository.findByStockNameContainingAndIsActiveTrueOrderByStockNameAsc("카카오")

        // Then
        assertThat(samsungResults).hasSize(1)
        assertThat(samsungResults[0].stockName).isEqualTo("삼성전자")

        assertThat(kakaoResults).hasSize(1)
        assertThat(kakaoResults[0].stockName).isEqualTo("카카오")
    }

    @Test
    fun `섹터 코드별로 주식을 조회할 수 있다`() {
        // Given
        val financeStock = DomesticStock.createKospi(
            stockCode = "055550",
            stockName = "신한지주",
            listingDate = LocalDate.of(2001, 9, 10),
            sectorCode = "FINANCE"
        )

        entityManager.persistAndFlush(samsungStock) // IT 섹터
        entityManager.persistAndFlush(skHynixStock) // IT 섹터
        entityManager.persistAndFlush(financeStock) // FINANCE 섹터

        // When
        val itStocks = repository.findBySectorCodeAndIsActiveTrueOrderByStockCodeAsc("IT")
        val financeStocks = repository.findBySectorCodeAndIsActiveTrueOrderByStockCodeAsc("FINANCE")

        // Then
        assertThat(itStocks).hasSize(2)
        assertThat(itStocks.map { it.stockName }).containsExactlyInAnyOrder("삼성전자", "SK하이닉스")

        assertThat(financeStocks).hasSize(1)
        assertThat(financeStocks[0].stockName).isEqualTo("신한지주")
    }

    @Test
    fun `종목코드 존재 여부를 확인할 수 있다`() {
        // Given
        entityManager.persistAndFlush(samsungStock)

        // When & Then
        assertThat(repository.existsByStockCode("005930")).isTrue()
        assertThat(repository.existsByStockCode("999999")).isFalse()
    }

    @Test
    fun `비활성 주식은 조회되지 않는다`() {
        // Given
        samsungStock.deactivate()
        entityManager.persistAndFlush(samsungStock)
        entityManager.persistAndFlush(skHynixStock)

        // When
        val activeStocks = repository.findByMarketTypeAndIsActiveTrueOrderByStockCodeAsc(DomesticMarketType.KOSPI)

        // Then
        assertThat(activeStocks).hasSize(1)
        assertThat(activeStocks[0].stockCode).isEqualTo("000660")
    }

    @Test
    fun `주식 종목 수를 카운트할 수 있다`() {
        // Given
        entityManager.persistAndFlush(samsungStock)
        entityManager.persistAndFlush(skHynixStock)
        entityManager.persistAndFlush(kakaoStock)

        // When
        val totalCount = repository.count()
        val kospiCount = repository.countByMarketTypeAndIsActiveTrue(DomesticMarketType.KOSPI)
        val kosdaqCount = repository.countByMarketTypeAndIsActiveTrue(DomesticMarketType.KOSDAQ)

        // Then
        assertThat(totalCount).isEqualTo(3)
        assertThat(kospiCount).isEqualTo(2)
        assertThat(kosdaqCount).isEqualTo(1)
    }
}