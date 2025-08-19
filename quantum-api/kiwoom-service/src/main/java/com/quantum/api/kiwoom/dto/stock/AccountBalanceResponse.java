package com.quantum.api.kiwoom.dto.stock;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * 계좌 잔고 조회 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AccountBalanceResponse {
    private String accountNumber;           // 계좌번호
    private BigDecimal cashBalance;         // 예수금
    private BigDecimal availableCash;       // 주문가능현금
    private BigDecimal totalAssetValue;     // 총평가금액
    private BigDecimal totalPurchaseAmount; // 총매입금액
    private BigDecimal totalEvalAmount;     // 총평가금액
    private BigDecimal totalProfitLoss;     // 총평가손익
    private BigDecimal profitLossRate;      // 수익률
    private BigDecimal d2Cash;              // D+2 예수금
    private Integer stockCount;             // 보유종목수
}