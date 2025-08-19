package com.quantum.kis.model;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.Builder;
import lombok.Getter;

/**
 * KIS 멀티 주식 조회 요청 모델
 *
 * <p>intstock-multprice API를 위한 요청 파라미터 생성 최대 30종목까지 한번에 조회 가능
 */
@Getter
@Builder
public class KisMultiStockRequest {

    /** 주식 종목 정보 */
    @Getter
    @Builder
    public static class StockItem {
        private final String marketDivCode; // 시장 구분 코드 (J: 주식, Q: 코스닥 등)
        private final String stockCode; // 종목 코드 (6자리)
    }

    private final List<StockItem> stockItems; // 조회할 종목 리스트 (최대 30개)

    /**
     * KIS API 요청 파라미터로 변환
     *
     * @return FID_COND_MRKT_DIV_CODE_1~30, FID_INPUT_ISCD_1~30 파라미터 맵
     */
    public Map<String, String> toQueryParams() {
        Map<String, String> params = new HashMap<>();

        if (stockItems == null || stockItems.isEmpty()) {
            throw new IllegalArgumentException("Stock items cannot be empty");
        }

        if (stockItems.size() > 30) {
            throw new IllegalArgumentException(
                    "Maximum 30 stock items allowed, got: " + stockItems.size());
        }

        // 1번부터 시작하는 인덱스로 파라미터 생성
        for (int i = 0; i < stockItems.size(); i++) {
            int paramIndex = i + 1;
            StockItem item = stockItems.get(i);

            params.put("FID_COND_MRKT_DIV_CODE_" + paramIndex, item.getMarketDivCode());
            params.put("FID_INPUT_ISCD_" + paramIndex, item.getStockCode());
        }

        return params;
    }

    /**
     * 편의 메서드: 종목 코드 리스트로부터 요청 객체 생성
     *
     * @param stockCodes 종목 코드 리스트 (기본 시장구분: J)
     * @return KisMultiStockRequest 객체
     */
    public static KisMultiStockRequest fromStockCodes(List<String> stockCodes) {
        return fromStockCodes(stockCodes, "J");
    }

    /**
     * 편의 메서드: 종목 코드 리스트와 시장구분으로부터 요청 객체 생성
     *
     * @param stockCodes 종목 코드 리스트
     * @param defaultMarketDivCode 기본 시장구분 코드
     * @return KisMultiStockRequest 객체
     */
    public static KisMultiStockRequest fromStockCodes(
            List<String> stockCodes, String defaultMarketDivCode) {
        if (stockCodes == null || stockCodes.isEmpty()) {
            throw new IllegalArgumentException("Stock codes cannot be empty");
        }

        List<StockItem> stockItems =
                stockCodes.stream()
                        .map(
                                code ->
                                        StockItem.builder()
                                                .marketDivCode(defaultMarketDivCode)
                                                .stockCode(code)
                                                .build())
                        .toList();

        return KisMultiStockRequest.builder().stockItems(stockItems).build();
    }

    /** 조회할 종목 수 반환 */
    public int getStockCount() {
        return stockItems != null ? stockItems.size() : 0;
    }

    /** 종목 코드 리스트 반환 */
    public List<String> getStockCodes() {
        return stockItems.stream().map(StockItem::getStockCode).toList();
    }
}
