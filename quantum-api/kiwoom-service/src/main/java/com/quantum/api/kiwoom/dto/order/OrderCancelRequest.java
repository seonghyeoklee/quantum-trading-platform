package com.quantum.api.kiwoom.dto.order;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 주문 취소 요청 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderCancelRequest {
    private String accountNumber;   // 계좌번호
    private String orderId;         // 원주문번호
    private String symbol;          // 종목코드
    private Integer quantity;       // 취소수량 (0: 전량취소)
}