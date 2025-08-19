package com.quantum.api.kiwoom.dto.stock;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 호가 조회 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderBookResponse {
    private String symbol;              // 종목코드
    private String stockName;           // 종목명
    private List<OrderBookItem> asks;   // 매도호가 (10호가)
    private List<OrderBookItem> bids;   // 매수호가 (10호가)
    private LocalDateTime timestamp;    // 시간
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class OrderBookItem {
        private BigDecimal price;       // 호가
        private Long quantity;          // 수량
        private Long remainQuantity;    // 잔량
        private BigDecimal changeRate;  // 대비율
    }
}