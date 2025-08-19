package com.quantum.api.kiwoom.dto.stock;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * 보유 종목 조회 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PositionResponse {
    private String symbol;                  // 종목코드
    private String stockName;               // 종목명
    private Integer quantity;               // 보유수량
    private BigDecimal averagePrice;        // 평균매입가
    private BigDecimal currentPrice;        // 현재가
    private BigDecimal purchaseAmount;      // 매입금액
    private BigDecimal evaluationAmount;    // 평가금액
    private BigDecimal profitLoss;          // 평가손익
    private BigDecimal profitLossRate;      // 수익률
    private Integer tradableQuantity;       // 매도가능수량
    private String accountNumber;           // 계좌번호
}