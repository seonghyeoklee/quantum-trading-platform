package com.quantum.api.kiwoom.dto.order;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * 주문 정정 요청 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderModifyRequest {
    private String accountNumber;   // 계좌번호
    private String orderId;         // 원주문번호
    private String symbol;          // 종목코드
    private Integer quantity;       // 정정수량
    private BigDecimal price;       // 정정가격
}