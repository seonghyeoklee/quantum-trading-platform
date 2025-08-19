package com.quantum.api.kiwoom.dto.stock;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 키움증권 주식 기본정보 요청 DTO
 * API: /api/dostk/stkinfo
 * api-id: ka10001
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "주식 기본정보 요청")
public class StockInfoRequest {
    
    @JsonProperty("stk_cd")
    @Schema(description = "종목코드", example = "005930", required = true, maxLength = 20)
    private String stockCode;
    
    /**
     * 종목코드 검증
     */
    public void validate() {
        if (stockCode == null || stockCode.trim().isEmpty()) {
            throw new IllegalArgumentException("종목코드는 필수입니다");
        }
        
        if (stockCode.length() > 20) {
            throw new IllegalArgumentException("종목코드는 20자 이하여야 합니다");
        }
    }
    
    /**
     * 거래소별 종목코드 포맷 변환
     * @param exchange 거래소 코드 (KRX, NXT, SOR)
     * @return 거래소별 종목코드
     */
    public String getFormattedStockCode(String exchange) {
        if (exchange == null || "KRX".equals(exchange)) {
            return stockCode;
        }
        
        return switch (exchange) {
            case "NXT" -> stockCode + "_NX";  // 넥스트
            case "SOR" -> stockCode + "_AL";  // 소프트웨어증권
            default -> stockCode;
        };
    }
}