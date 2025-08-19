package com.quantum.api.infrastructure.mapper;

import com.quantum.core.domain.model.kis.KisRawDataStore;
import com.quantum.core.domain.model.kis.KisStockPriceData;
import com.quantum.kis.model.KisCurrentPriceResponse;
import org.mapstruct.Mapper;

/** MapStruct 기반 KIS 데이터 매퍼 - 간단한 변환 */
@Mapper(componentModel = "spring")
public interface KisDataMapper {

    /** 간단한 팩토리 메서드 (생성자 사용) */
    default KisStockPriceData toEntity(String symbol, KisCurrentPriceResponse response) {
        var output = response.output();
        return new KisStockPriceData(
                symbol,
                response.resultCode(),
                response.messageCode(),
                response.message(),
                output.stockStatusCode(),
                output.marginRate(),
                output.representativeMarketName(),
                output.newHighLowClassCode(),
                output.stockKoreanName(),
                output.temporaryStopYn(),
                output.openPriceRangeContinueYn(),
                output.closePriceRangeContinueYn(),
                output.creditAvailableYn(),
                output.guaranteeRateClassCode(),
                output.elwPublicYn(),
                output.currentPrice(),
                output.previousDayComparison(),
                output.previousDayComparisonSign(),
                output.previousDayChangeRate(),
                output.accumulatedTransactionAmount(),
                output.accumulatedVolume(),
                output.previousVolumeComparisonRate(),
                output.openPrice(),
                output.highPrice(),
                output.lowPrice(),
                output.maxPrice(),
                output.minPrice(),
                output.standardPrice(),
                output.weightedAveragePrice(),
                output.foreignerHoldingRate(),
                output.foreignerNetBuyQuantity(),
                output.programNetBuyQuantity(),
                output.pivotSecondResistancePrice(),
                output.pivotFirstResistancePrice(),
                output.pivotPointValue(),
                output.pivotFirstSupportPrice(),
                output.pivotSecondSupportPrice(),
                output.resistanceValue(),
                output.supportValue(),
                output.capitalFund(),
                output.restrictionWidthPrice(),
                output.stockFaceAmount(),
                output.stockSuspendPrice(),
                output.askPriceUnit(),
                output.htsDealQuantityUnitValue(),
                output.listedStockCount(),
                output.htsMarketCap(),
                output.per(),
                output.pbr(),
                output.settlementMonth(),
                output.volumeTurnoverRate(),
                output.eps(),
                output.bps(),
                output.day250HighPrice(),
                output.day250HighPriceDate(),
                output.day250HighPriceVsCurrentRate(),
                output.day250LowPrice(),
                output.day250LowPriceDate(),
                output.day250LowPriceVsCurrentRate(),
                output.yearHighPrice(),
                output.yearHighPriceVsCurrentRate(),
                output.yearHighPriceDate(),
                output.yearLowPrice(),
                output.yearLowPriceVsCurrentRate(),
                output.yearLowPriceDate(),
                output.week52HighPrice(),
                output.week52HighPriceVsCurrentRate(),
                output.week52HighPriceDate(),
                output.week52LowPrice(),
                output.week52LowPriceVsCurrentRate(),
                output.week52LowPriceDate(),
                output.wholeLoanRemainRate(),
                output.shortSellingAvailableYn(),
                output.stockShortCode(),
                output.faceAmountCurrencyName(),
                output.capitalFundCurrencyName(),
                output.approachRate(),
                output.foreignerHoldingQuantity(),
                output.viClassCode(),
                output.overtimeViClassCode(),
                output.lastShortSellingQuantity(),
                output.investmentCautionYn(),
                output.marketWarningClassCode(),
                output.shortOverheatingYn(),
                output.settlementTradingYn(),
                output.managementIssueClassCode());
    }

    /** JSON Store 백업용 간단한 매핑 */
    default KisRawDataStore toRawStore(String symbol, KisCurrentPriceResponse response) {
        return KisRawDataStore.createCurrentPriceStore(symbol, convertToJson(response));
    }

    /** JSON 직렬화 헬퍼 메서드 */
    default String convertToJson(KisCurrentPriceResponse response) {
        try {
            com.fasterxml.jackson.databind.ObjectMapper mapper =
                    new com.fasterxml.jackson.databind.ObjectMapper();
            return mapper.writeValueAsString(response);
        } catch (Exception e) {
            return "{}";
        }
    }
}
