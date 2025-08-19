package com.quantum.kis.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * KIS 멀티 주식 조회 응답 모델
 *
 * <p>intstock-multprice API 응답 구조 최대 30종목의 시세 정보를 담고 있음
 */
public record KisMultiStockResponse(
        @JsonProperty("rt_cd") String resultCode, // 결과 코드
        @JsonProperty("msg_cd") String messageCode, // 메시지 코드
        @JsonProperty("msg1") String message, // 응답 메시지
        @JsonProperty("output") List<KisMultiStockItem> output // 멀티 주식 시세 데이터
        ) {

    /** API 호출 성공 여부 확인 */
    public boolean isSuccess() {
        return "0".equals(resultCode);
    }

    /** 조회된 종목 수 반환 */
    public int getStockCount() {
        return output != null ? output.size() : 0;
    }

    /** 특정 종목코드의 시세 정보 조회 */
    public KisMultiStockItem getStockItem(String stockCode) {
        if (output == null) {
            return null;
        }

        return output.stream()
                .filter(item -> stockCode.equals(item.stockCode()))
                .findFirst()
                .orElse(null);
    }
}
