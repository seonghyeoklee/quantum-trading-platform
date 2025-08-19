package com.quantum.api.kiwoom.dto.stock;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 주문 내역 조회 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderHistoryResponse {
    private String orderId;             // 주문번호
    private String symbol;              // 종목코드
    private String stockName;           // 종목명
    private String orderType;           // 매도매수구분
    private String orderStatus;         // 주문상태
    private Integer orderQuantity;      // 주문수량
    private BigDecimal orderPrice;      // 주문가격
    private Integer executedQuantity;   // 체결수량
    private BigDecimal executedPrice;   // 체결가격
    private LocalDateTime orderTime;    // 주문시간
    private LocalDateTime executedTime; // 체결시간
}