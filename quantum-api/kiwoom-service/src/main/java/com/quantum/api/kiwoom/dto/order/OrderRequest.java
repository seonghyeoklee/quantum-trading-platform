package com.quantum.api.kiwoom.dto.order;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * 주식 주문 요청 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderRequest {
    private String accountNumber;   // 계좌번호
    private String symbol;          // 종목코드 (6자리)
    private OrderType orderType;    // 주문 구분 (BUY: 매수, SELL: 매도)
    private PriceType priceType;    // 가격 구분 (MARKET: 시장가, LIMIT: 지정가)
    private Integer quantity;       // 주문 수량
    private BigDecimal price;       // 주문 가격 (지정가일 경우)
    
    public enum OrderType {
        BUY("01"),      // 매수
        SELL("02");     // 매도
        
        private final String code;
        
        OrderType(String code) {
            this.code = code;
        }
        
        public String getCode() {
            return code;
        }
    }
    
    public enum PriceType {
        MARKET("01"),   // 시장가
        LIMIT("00");    // 지정가
        
        private final String code;
        
        PriceType(String code) {
            this.code = code;
        }
        
        public String getCode() {
            return code;
        }
    }
}