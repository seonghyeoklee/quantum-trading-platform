package com.quantum.web.dto;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * 자동매매 전략 신호 DTO
 * 
 * Python 전략 엔진에서 생성된 매매신호를 Java로 전송하기 위한 데이터 모델
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TradingSignalDto {
    
    /**
     * 전략명
     */
    @NotBlank(message = "전략명은 필수입니다")
    @Size(max = 100, message = "전략명은 100자를 초과할 수 없습니다")
    private String strategyName;
    
    /**
     * 종목코드 (6자리)
     */
    @NotBlank(message = "종목코드는 필수입니다")
    @Pattern(regexp = "^[0-9]{6}$", message = "종목코드는 6자리 숫자여야 합니다")
    private String symbol;
    
    /**
     * 매매신호 타입
     */
    @NotBlank(message = "신호 타입은 필수입니다")
    @Pattern(regexp = "^(BUY|SELL|HOLD|CLOSE)$", 
             message = "신호 타입은 BUY, SELL, HOLD, CLOSE 중 하나여야 합니다")
    private String signalType;
    
    /**
     * 신호 강도
     */
    @NotBlank(message = "신호 강도는 필수입니다")
    @Pattern(regexp = "^(WEAK|MODERATE|STRONG)$", 
             message = "신호 강도는 WEAK, MODERATE, STRONG 중 하나여야 합니다")
    private String strength;
    
    /**
     * 현재가
     */
    @NotNull(message = "현재가는 필수입니다")
    @DecimalMin(value = "0.0", inclusive = false, message = "현재가는 0보다 커야 합니다")
    private BigDecimal currentPrice;
    
    /**
     * 목표가 (선택적)
     */
    @DecimalMin(value = "0.0", inclusive = false, message = "목표가는 0보다 커야 합니다")
    private BigDecimal targetPrice;
    
    /**
     * 손절가 (선택적)
     */
    @DecimalMin(value = "0.0", inclusive = false, message = "손절가는 0보다 커야 합니다")
    private BigDecimal stopLoss;
    
    /**
     * 매매 수량 (선택적)
     */
    @Min(value = 1, message = "수량은 1 이상이어야 합니다")
    private Integer quantity;
    
    /**
     * 포트폴리오 대비 비중 (선택적, 0.0 ~ 1.0)
     */
    @DecimalMin(value = "0.0", message = "비중은 0.0 이상이어야 합니다")
    @DecimalMax(value = "1.0", message = "비중은 1.0 이하여야 합니다")
    private BigDecimal quantityRatio;
    
    /**
     * 신호 신뢰도 (0.0 ~ 1.0)
     */
    @NotNull(message = "신뢰도는 필수입니다")
    @DecimalMin(value = "0.0", message = "신뢰도는 0.0 이상이어야 합니다")
    @DecimalMax(value = "1.0", message = "신뢰도는 1.0 이하여야 합니다")
    private BigDecimal confidence;
    
    /**
     * 신호 발생 이유
     */
    @NotBlank(message = "신호 발생 이유는 필수입니다")
    @Size(max = 500, message = "신호 발생 이유는 500자를 초과할 수 없습니다")
    private String reason;
    
    /**
     * 신호 생성 시간
     */
    @NotNull(message = "신호 생성 시간은 필수입니다")
    private LocalDateTime timestamp;
    
    /**
     * 신호 유효 기한 (선택적)
     */
    private LocalDateTime validUntil;
    
    /**
     * 모의투자 여부
     */
    @NotNull(message = "실행 모드는 필수입니다")
    private Boolean dryRun = true;
    
    /**
     * 전략 파라미터 (JSON 문자열)
     */
    private String strategyParams;
    
    /**
     * 기술적 지표 값들 (JSON 문자열)
     */
    private String technicalIndicators;
    
    /**
     * 추가 정보 (JSON 문자열)
     */
    private String additionalInfo;
    
    /**
     * 신호 우선순위 (1: 최고, 5: 최저)
     */
    @Min(value = 1, message = "우선순위는 1 이상이어야 합니다")
    @Max(value = 5, message = "우선순위는 5 이하여야 합니다")
    private Integer priority = 3;  // 기본값: 보통
    
    /**
     * 신호가 유효한지 확인
     * 
     * @return 유효하면 true, 만료되었으면 false
     */
    public boolean isValid() {
        if (validUntil == null) {
            return true;  // 유효기한이 없으면 항상 유효
        }
        return LocalDateTime.now().isBefore(validUntil);
    }
    
    /**
     * 매수 신호인지 확인
     * 
     * @return 매수 신호면 true
     */
    public boolean isBuySignal() {
        return "BUY".equals(signalType);
    }
    
    /**
     * 매도 신호인지 확인
     * 
     * @return 매도 신호면 true
     */
    public boolean isSellSignal() {
        return "SELL".equals(signalType);
    }
    
    /**
     * 신호 강도가 강한지 확인
     * 
     * @return 강한 신호면 true
     */
    public boolean isStrongSignal() {
        return "STRONG".equals(strength);
    }
    
    /**
     * 신뢰도가 임계치 이상인지 확인
     * 
     * @param threshold 임계치 (0.0 ~ 1.0)
     * @return 임계치 이상이면 true
     */
    public boolean isConfidenceAbove(double threshold) {
        return confidence.doubleValue() >= threshold;
    }
    
    /**
     * 실행 가능한 신호인지 확인 (유효성 + 신뢰도 체크)
     * 
     * @param minConfidence 최소 신뢰도
     * @return 실행 가능하면 true
     */
    public boolean isExecutable(double minConfidence) {
        return isValid() && 
               isConfidenceAbove(minConfidence) && 
               (isBuySignal() || isSellSignal());
    }
    
    /**
     * 키움증권 API용 주문 구분 반환
     * 
     * @return 주문 구분 ("01": 매수, "02": 매도)
     */
    public String getKiwoomOrderSide() {
        switch (signalType) {
            case "BUY":
                return "01";  // 매수
            case "SELL":
            case "CLOSE":
                return "02";  // 매도
            default:
                throw new IllegalStateException("주문으로 변환할 수 없는 신호 타입: " + signalType);
        }
    }
    
    /**
     * 신호 요약 정보 반환
     * 
     * @return 신호 요약 문자열
     */
    public String getSummary() {
        return String.format("[%s] %s %s (신뢰도: %.1f%%, 가격: %s원)", 
                strategyName, symbol, signalType, 
                confidence.doubleValue() * 100, 
                currentPrice.toString());
    }

    /**
     * 매매신호 수신 응답 DTO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ReceiveResponse {
        
        @NotBlank
        private String signalId; // 생성된 신호 ID
        
        @NotBlank
        private String status; // RECEIVED, VALIDATED, REJECTED, PROCESSED
        
        private String message;
        
        private LocalDateTime receivedAt;
        
        private LocalDateTime processedAt;
        
        // 매칭된 자동매매 설정 정보 (있는 경우)
        private String matchedConfigId;
        private String matchedConfigName;
        
        // 처리 결과 정보
        private ProcessingResult processingResult;
    }

    /**
     * 신호 처리 결과 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ProcessingResult {
        
        private Boolean willExecute; // 주문 실행 여부
        
        private String executionReason; // 실행/비실행 이유
        
        private BigDecimal calculatedQuantity; // 계산된 주문 수량
        
        private BigDecimal calculatedAmount; // 계산된 주문 금액
        
        // 리스크 검증 결과
        private RiskValidationResult riskValidation;
    }

    /**
     * 리스크 검증 결과 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RiskValidationResult {
        
        private Boolean passed; // 리스크 검증 통과 여부
        
        private String riskLevel; // LOW, MEDIUM, HIGH, CRITICAL
        
        private BigDecimal riskScore; // 0.0 ~ 1.0
        
        private String[] warnings; // 경고 메시지들
        
        private String[] blockers; // 차단 사유들
    }

    /**
     * 신호 통계 DTO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SignalStatistics {
        
        private Long totalSignals;
        
        private Long processedSignals;
        
        private Long executedSignals;
        
        private Long rejectedSignals;
        
        private BigDecimal averageConfidence;
        
        private BigDecimal successRate;
        
        // 전략별 통계
        private Map<String, StrategyStatistics> strategyStats;
        
        // 시간별 통계
        private Map<String, Long> hourlyStats;
        
        private LocalDateTime lastSignalTime;
    }

    /**
     * 전략별 통계 내부 클래스
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class StrategyStatistics {
        
        private String strategyName;
        
        private Long totalSignals;
        
        private Long successfulSignals;
        
        private BigDecimal successRate;
        
        private BigDecimal averageConfidence;
        
        private BigDecimal totalProfit;
        
        private LocalDateTime lastSignalTime;
    }
}