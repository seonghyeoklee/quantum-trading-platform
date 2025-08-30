package com.quantum.web.dto;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 주문 실행 결과 DTO
 * 
 * 매매신호 처리 결과를 클라이언트에게 반환하기 위한 데이터 모델
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderExecutionResultDto {
    
    /**
     * 실행 결과 상태
     */
    private ExecutionStatus status;
    
    /**
     * 처리 메시지
     */
    private String message;
    
    /**
     * 원본 신호 정보
     */
    private TradingSignalDto originalSignal;
    
    /**
     * 생성된 주문 ID (실제 주문이 생성된 경우)
     */
    private String orderId;
    
    /**
     * 키움증권 주문번호 (실제 주문이 체결된 경우)
     */
    private String kiwoomOrderNumber;
    
    /**
     * 실행된 수량
     */
    private Integer executedQuantity;
    
    /**
     * 실행된 가격
     */
    private BigDecimal executedPrice;
    
    /**
     * 총 거래 금액
     */
    private BigDecimal totalAmount;
    
    /**
     * 수수료
     */
    private BigDecimal commission;
    
    /**
     * 세금
     */
    private BigDecimal tax;
    
    /**
     * 순 거래 금액 (거래금액 - 수수료 - 세금)
     */
    private BigDecimal netAmount;
    
    /**
     * 실행 시간
     */
    private LocalDateTime executedAt;
    
    /**
     * 소요 시간 (밀리초)
     */
    private Long processingTimeMs;
    
    /**
     * 에러 코드 (실패 시)
     */
    private String errorCode;
    
    /**
     * 에러 상세 메시지 (실패 시)
     */
    private String errorDetail;
    
    /**
     * 실행 모드 (실투자/모의투자)
     */
    private Boolean dryRun;
    
    /**
     * 잔고 정보 업데이트 여부
     */
    private Boolean balanceUpdated;
    
    /**
     * 포트폴리오 업데이트 여부
     */
    private Boolean portfolioUpdated;
    
    /**
     * 추가 실행 정보 (JSON)
     */
    private String additionalInfo;
    
    /**
     * 실행 결과 상태 열거형
     */
    public enum ExecutionStatus {
        SUCCESS,           // 성공적으로 실행됨
        PARTIAL_SUCCESS,   // 부분적으로 실행됨
        PENDING,           // 처리 중 (비동기)
        REJECTED,          // 거부됨 (조건 미충족)
        FAILED,            // 실행 실패
        TIMEOUT,           // 시간 초과
        CANCELLED          // 취소됨
    }
    
    /**
     * 성공적인 실행 결과 생성
     * 
     * @param signal 원본 신호
     * @param orderId 주문 ID
     * @param quantity 실행 수량
     * @param price 실행 가격
     * @return 성공 결과
     */
    public static OrderExecutionResultDto success(
            TradingSignalDto signal, 
            String orderId, 
            Integer quantity, 
            BigDecimal price) {
        
        BigDecimal totalAmount = price.multiply(BigDecimal.valueOf(quantity));
        
        return OrderExecutionResultDto.builder()
                .status(ExecutionStatus.SUCCESS)
                .message("매매신호가 성공적으로 처리되었습니다")
                .originalSignal(signal)
                .orderId(orderId)
                .executedQuantity(quantity)
                .executedPrice(price)
                .totalAmount(totalAmount)
                .executedAt(LocalDateTime.now())
                .dryRun(signal.getDryRun())
                .balanceUpdated(true)
                .portfolioUpdated(true)
                .build();
    }
    
    /**
     * 실패한 실행 결과 생성
     * 
     * @param signal 원본 신호
     * @param reason 실패 사유
     * @param errorCode 에러 코드
     * @return 실패 결과
     */
    public static OrderExecutionResultDto failure(
            TradingSignalDto signal, 
            String reason, 
            String errorCode) {
        
        return OrderExecutionResultDto.builder()
                .status(ExecutionStatus.FAILED)
                .message("매매신호 처리에 실패했습니다: " + reason)
                .originalSignal(signal)
                .errorCode(errorCode)
                .errorDetail(reason)
                .executedAt(LocalDateTime.now())
                .dryRun(signal.getDryRun())
                .balanceUpdated(false)
                .portfolioUpdated(false)
                .build();
    }
    
    /**
     * 거부된 실행 결과 생성
     * 
     * @param signal 원본 신호
     * @param reason 거부 사유
     * @return 거부 결과
     */
    public static OrderExecutionResultDto rejected(
            TradingSignalDto signal, 
            String reason) {
        
        return OrderExecutionResultDto.builder()
                .status(ExecutionStatus.REJECTED)
                .message("매매신호가 거부되었습니다: " + reason)
                .originalSignal(signal)
                .errorDetail(reason)
                .executedAt(LocalDateTime.now())
                .dryRun(signal.getDryRun())
                .balanceUpdated(false)
                .portfolioUpdated(false)
                .build();
    }
    
    /**
     * 모의투자 실행 결과 생성
     * 
     * @param signal 원본 신호
     * @param quantity 가상 실행 수량
     * @param price 가상 실행 가격
     * @return 모의투자 결과
     */
    public static OrderExecutionResultDto dryRun(
            TradingSignalDto signal, 
            Integer quantity, 
            BigDecimal price) {
        
        BigDecimal totalAmount = price.multiply(BigDecimal.valueOf(quantity));
        
        return OrderExecutionResultDto.builder()
                .status(ExecutionStatus.SUCCESS)
                .message("모의투자로 성공적으로 처리되었습니다")
                .originalSignal(signal)
                .orderId("DRY_RUN_" + System.currentTimeMillis())
                .executedQuantity(quantity)
                .executedPrice(price)
                .totalAmount(totalAmount)
                .commission(totalAmount.multiply(BigDecimal.valueOf(0.00015)))  // 0.015% 수수료
                .tax(signal.isSellSignal() ? totalAmount.multiply(BigDecimal.valueOf(0.0025)) : BigDecimal.ZERO)  // 매도시 0.25% 세금
                .executedAt(LocalDateTime.now())
                .dryRun(true)
                .balanceUpdated(false)  // 모의투자는 실제 잔고 업데이트하지 않음
                .portfolioUpdated(false)
                .build();
    }
    
    /**
     * 성공적인 실행인지 확인
     * 
     * @return 성공이면 true
     */
    public boolean isSuccessful() {
        return status == ExecutionStatus.SUCCESS || status == ExecutionStatus.PARTIAL_SUCCESS;
    }
    
    /**
     * 실패한 실행인지 확인
     * 
     * @return 실패면 true
     */
    public boolean isFailed() {
        return status == ExecutionStatus.FAILED || status == ExecutionStatus.TIMEOUT;
    }
    
    /**
     * 거부된 실행인지 확인
     * 
     * @return 거부되었으면 true
     */
    public boolean isRejected() {
        return status == ExecutionStatus.REJECTED;
    }
    
    /**
     * 처리 중인지 확인
     * 
     * @return 처리 중이면 true
     */
    public boolean isPending() {
        return status == ExecutionStatus.PENDING;
    }
    
    /**
     * 실행 수익/손실 계산 (매도의 경우)
     * 
     * @param originalBuyPrice 원래 매수 가격
     * @return 수익률 (양수: 수익, 음수: 손실)
     */
    public BigDecimal calculateProfitLoss(BigDecimal originalBuyPrice) {
        if (executedPrice == null || originalBuyPrice == null) {
            return BigDecimal.ZERO;
        }
        
        return executedPrice.subtract(originalBuyPrice)
                .divide(originalBuyPrice, 4, BigDecimal.ROUND_HALF_UP)
                .multiply(BigDecimal.valueOf(100));  // 백분율로 변환
    }
    
    /**
     * 순 실행 금액 계산
     */
    public void calculateNetAmount() {
        if (totalAmount == null) {
            this.netAmount = BigDecimal.ZERO;
            return;
        }
        
        BigDecimal totalCost = BigDecimal.ZERO;
        
        if (commission != null) {
            totalCost = totalCost.add(commission);
        }
        
        if (tax != null) {
            totalCost = totalCost.add(tax);
        }
        
        this.netAmount = totalAmount.subtract(totalCost);
    }
    
    /**
     * 실행 결과 요약 정보
     * 
     * @return 요약 문자열
     */
    public String getSummary() {
        String mode = Boolean.TRUE.equals(dryRun) ? "[모의투자]" : "[실투자]";
        String statusText = status.name();
        
        if (isSuccessful()) {
            return String.format("%s %s - %s %d주 %s원 (총 %s원)", 
                    mode, statusText,
                    originalSignal.getSymbol(), 
                    executedQuantity, 
                    executedPrice, 
                    totalAmount);
        } else {
            return String.format("%s %s - %s (%s)", 
                    mode, statusText, 
                    originalSignal.getSymbol(), 
                    message);
        }
    }
}