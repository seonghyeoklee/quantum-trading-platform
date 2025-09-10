package com.quantum.stock.presentation.dto

import com.quantum.stock.domain.DomesticStocksDetail

/**
 * 프론트엔드 차트에 필요한 데이터만 포함한 DTO (DailyChartDataResponse 형태)
 */
data class DailyChartDataResponse(
    val stockCode: String,
    val tradeDate: String,      // YYYY-MM-DD 형태
    val openPrice: Long,
    val highPrice: Long,
    val lowPrice: Long,
    val closePrice: Long,
    val volume: Long,
    val amount: Long? = null
) {
    companion object {
        /**
         * DomesticStocksDetail을 DailyChartDataResponse로 변환
         */
        fun fromDomesticStocksDetail(detail: DomesticStocksDetail): DailyChartDataResponse? {
            // 차트 데이터가 아니거나 거래일이 없으면 null 반환
            if (!detail.isChartData() || detail.tradeDate == null) {
                return null
            }
            
            val openPrice = detail.getOpenPrice() ?: return null
            val highPrice = detail.getHighPrice() ?: return null
            val lowPrice = detail.getLowPrice() ?: return null
            val closePrice = detail.getClosePrice() ?: return null
            
            // OHLCV 데이터에서 volume과 amount 가져오기
            val ohlcvData = detail.getOhlcvData()
            val volume = ohlcvData.volume ?: return null
            
            // 유효한 OHLC 데이터만 변환
            if (openPrice <= 0 || highPrice <= 0 || lowPrice <= 0 || closePrice <= 0) {
                return null
            }
            
            return DailyChartDataResponse(
                stockCode = detail.stockCode,
                tradeDate = detail.tradeDate!!.toString(), // LocalDate를 YYYY-MM-DD 문자열로 변환
                openPrice = openPrice,
                highPrice = highPrice,
                lowPrice = lowPrice,
                closePrice = closePrice,
                volume = volume,
                amount = null
            )
        }
        
        /**
         * DomesticStocksDetail 리스트를 DailyChartDataResponse 리스트로 변환
         */
        fun fromDomesticStocksDetailList(details: List<DomesticStocksDetail>): List<DailyChartDataResponse> {
            return details.mapNotNull { fromDomesticStocksDetail(it) }
                .sortedBy { it.tradeDate } // 날짜순 정렬
        }
    }
}