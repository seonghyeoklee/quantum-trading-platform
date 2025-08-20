package com.quantum.api.kiwoom.dto.order;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 주식 주문 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderResponse {
    private String orderId;         // 주문번호
    private String accountNumber;   // 계좌번호
    private String symbol;          // 종목코드
    private String stockName;       // 종목명
    private String orderType;       // 매수/매도 구분
    private String orderStatus;     // 주문상태 (접수/체결/정정/취소)
    private Integer orderQuantity;  // 주문수량
    private Integer executedQuantity; // 체결수량
    private String orderPrice;      // 주문가격
    private String executedPrice;   // 체결가격
    private LocalDateTime orderTime; // 주문시간
    private String message;         // 응답 메시지
    private boolean success;        // 성공 여부
}