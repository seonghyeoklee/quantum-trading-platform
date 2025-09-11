package com.quantum.stock.domain

import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.assertj.core.api.Assertions.*
import java.time.LocalDate
import java.time.LocalDateTime

/**
 * DomesticStock 도메인 엔티티 단위 테스트
 * 
 * 국내주식 도메인 로직의 정확성을 검증
 */
class DomesticStockTest {

    private lateinit var kospiStock: DomesticStock
    private lateinit var kosdaqStock: DomesticStock

    @BeforeEach
    fun setUp() {
        kospiStock = DomesticStock(
            stockCode = "005930",
            stockName = "삼성전자",
            marketType = DomesticMarketType.KOSPI,
            isinCode = "KR7005930003",
            sectorCode = "IT0001",
            listingDate = LocalDate.of(1975, 6, 11)
        )

        kosdaqStock = DomesticStock(
            stockCode = "035720",
            stockName = "카카오",
            marketType = DomesticMarketType.KOSDAQ,
            isinCode = "KR7035720002",
            sectorCode = "IT0002",
            listingDate = LocalDate.of(2017, 7, 10)
        )
    }

    // ========== 생성 및 초기화 테스트 ==========

    @Test
    fun `DomesticStock 생성 시 기본값들이 올바르게 설정된다`() {
        // Given & When
        val stock = DomesticStock(
            stockCode = "123456",
            stockName = "테스트주식",
            marketType = DomesticMarketType.KOSPI
        )

        // Then
        assertThat(stock.stockCode).isEqualTo("123456")
        assertThat(stock.stockName).isEqualTo("테스트주식")
        assertThat(stock.marketType).isEqualTo(DomesticMarketType.KOSPI)
        assertThat(stock.isActive).isTrue() // 기본값
        assertThat(stock.isinCode).isNull()
        assertThat(stock.sectorCode).isNull()
        assertThat(stock.listingDate).isNull()
        assertThat(stock.rawData).isNull()
        assertThat(stock.stockDetails).isEmpty()
    }

    // ========== 시장구분 확인 테스트 ==========

    @Test
    fun `KOSPI 종목임을 올바르게 확인할 수 있다`() {
        // Given & When & Then
        assertThat(kospiStock.isKospi()).isTrue()
        assertThat(kospiStock.isKosdaq()).isFalse()
    }

    @Test
    fun `KOSDAQ 종목임을 올바르게 확인할 수 있다`() {
        // Given & When & Then
        assertThat(kosdaqStock.isKospi()).isFalse()
        assertThat(kosdaqStock.isKosdaq()).isTrue()
    }

    // ========== 활성 상태 관리 테스트 ==========

    @Test
    fun `새로 생성된 종목은 기본적으로 활성 상태이다`() {
        // Given & When & Then
        assertThat(kospiStock.isActiveStock()).isTrue()
        assertThat(kospiStock.isActive).isTrue()
    }

    @Test
    fun `종목을 비활성화할 수 있다`() {
        // Given
        assertThat(kospiStock.isActive).isTrue()

        // When
        kospiStock.deactivate()

        // Then
        assertThat(kospiStock.isActive).isFalse()
        assertThat(kospiStock.isActiveStock()).isFalse()
    }

    @Test
    fun `비활성화된 종목을 다시 활성화할 수 있다`() {
        // Given
        kospiStock.deactivate()
        assertThat(kospiStock.isActive).isFalse()

        // When
        kospiStock.activate()

        // Then
        assertThat(kospiStock.isActive).isTrue()
        assertThat(kospiStock.isActiveStock()).isTrue()
    }

    // ========== 종목 정보 업데이트 테스트 ==========

    @Test
    fun `종목명을 업데이트할 수 있다`() {
        // Given
        val newName = "삼성전자우"

        // When
        kospiStock.updateStockInfo(stockName = newName)

        // Then
        assertThat(kospiStock.stockName).isEqualTo(newName)
        // 다른 속성들은 변경되지 않음
        assertThat(kospiStock.stockCode).isEqualTo("005930")
        assertThat(kospiStock.marketType).isEqualTo(DomesticMarketType.KOSPI)
    }

    @Test
    fun `시장구분을 업데이트할 수 있다`() {
        // Given & When
        kospiStock.updateStockInfo(marketType = DomesticMarketType.KOSDAQ)

        // Then
        assertThat(kospiStock.marketType).isEqualTo(DomesticMarketType.KOSDAQ)
        assertThat(kospiStock.isKosdaq()).isTrue()
        assertThat(kospiStock.isKospi()).isFalse()
    }

    @Test
    fun `업종코드를 업데이트할 수 있다`() {
        // Given
        val newSectorCode = "FI0001"

        // When
        kospiStock.updateStockInfo(sectorCode = newSectorCode)

        // Then
        assertThat(kospiStock.sectorCode).isEqualTo(newSectorCode)
    }

    @Test
    fun `상장일을 업데이트할 수 있다`() {
        // Given
        val newListingDate = LocalDate.of(2020, 1, 1)

        // When
        kospiStock.updateStockInfo(listingDate = newListingDate)

        // Then
        assertThat(kospiStock.listingDate).isEqualTo(newListingDate)
    }

    @Test
    fun `여러 속성을 한번에 업데이트할 수 있다`() {
        // Given
        val newName = "새로운종목명"
        val newMarketType = DomesticMarketType.KOSDAQ
        val newSectorCode = "NEW001"
        val newListingDate = LocalDate.of(2023, 1, 1)

        // When
        kospiStock.updateStockInfo(
            stockName = newName,
            marketType = newMarketType,
            sectorCode = newSectorCode,
            listingDate = newListingDate
        )

        // Then
        assertThat(kospiStock.stockName).isEqualTo(newName)
        assertThat(kospiStock.marketType).isEqualTo(newMarketType)
        assertThat(kospiStock.sectorCode).isEqualTo(newSectorCode)
        assertThat(kospiStock.listingDate).isEqualTo(newListingDate)
    }

    @Test
    fun `null 값으로 업데이트 시 기존 값이 유지된다`() {
        // Given
        val originalName = kospiStock.stockName
        val originalMarketType = kospiStock.marketType

        // When - null 값들로 업데이트 시도
        kospiStock.updateStockInfo(
            stockName = null,
            marketType = null,
            sectorCode = null,
            listingDate = null
        )

        // Then - 기존 값들이 유지됨
        assertThat(kospiStock.stockName).isEqualTo(originalName)
        assertThat(kospiStock.marketType).isEqualTo(originalMarketType)
    }

    // ========== 종목 요약 정보 테스트 ==========

    @Test
    fun `활성 종목의 요약 정보를 올바르게 생성한다`() {
        // Given & When
        val summary = kospiStock.getSummary()

        // Then
        assertThat(summary).isEqualTo("005930 (삼성전자) [KOSPI] - 활성")
    }

    @Test
    fun `비활성 종목의 요약 정보를 올바르게 생성한다`() {
        // Given
        kospiStock.deactivate()

        // When
        val summary = kospiStock.getSummary()

        // Then
        assertThat(summary).isEqualTo("005930 (삼성전자) [KOSPI] - 비활성")
    }

    // ========== 최신 상세정보 조회 테스트 ==========

    @Test
    fun `상세정보가 없을 때 getLatestDetail은 null을 반환한다`() {
        // Given & When & Then
        assertThat(kospiStock.getLatestDetail()).isNull()
    }

    @Test
    fun `stockDetails 컬렉션이 올바르게 초기화된다`() {
        // Given & When & Then
        assertThat(kospiStock.stockDetails).isNotNull()
        assertThat(kospiStock.stockDetails).isEmpty()
    }
}

/**
 * DomesticMarketType enum 테스트
 */
class DomesticMarketTypeTest {

    @Test
    fun `DomesticMarketType enum 값들이 올바르게 정의되어 있다`() {
        assertThat(DomesticMarketType.values()).containsExactly(
            DomesticMarketType.KOSPI,
            DomesticMarketType.KOSDAQ
        )
    }

    @Test
    fun `각 시장구분의 이름이 올바르다`() {
        assertThat(DomesticMarketType.KOSPI.name).isEqualTo("KOSPI")
        assertThat(DomesticMarketType.KOSDAQ.name).isEqualTo("KOSDAQ")
    }
}

/**
 * DataQuality enum 테스트
 */
class DataQualityTest {

    @Test
    fun `DataQuality enum 값들이 올바르게 정의되어 있다`() {
        assertThat(DataQuality.values()).containsExactly(
            DataQuality.EXCELLENT,
            DataQuality.GOOD,
            DataQuality.FAIR,
            DataQuality.POOR
        )
    }

    @Test
    fun `DataQuality enum 순서가 품질 순으로 정렬되어 있다`() {
        val qualities = DataQuality.values().toList()
        
        // 순서: EXCELLENT > GOOD > FAIR > POOR
        assertThat(qualities.indexOf(DataQuality.EXCELLENT))
            .isLessThan(qualities.indexOf(DataQuality.GOOD))
        assertThat(qualities.indexOf(DataQuality.GOOD))
            .isLessThan(qualities.indexOf(DataQuality.FAIR))
        assertThat(qualities.indexOf(DataQuality.FAIR))
            .isLessThan(qualities.indexOf(DataQuality.POOR))
    }
}