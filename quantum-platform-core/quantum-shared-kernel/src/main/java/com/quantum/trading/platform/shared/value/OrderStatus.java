package com.quantum.trading.platform.shared.value;

/**
 * 주문 상태 열거형
 * 
 * 주문의 생명주기를 나타내는 상태들
 */
public enum OrderStatus {
    /**
     * 대기 중 - 주문이 생성되었지만 아직 증권사에 전송되지 않음
     */
    PENDING("대기중"),
    
    /**
     * 검증 중 - 포트폴리오 검증, 리스크 체크 등 진행 중
     */
    VALIDATING("검증중"),
    
    /**
     * 제출됨 - 증권사 API에 주문이 전송됨
     */
    SUBMITTED("제출됨"),
    
    /**
     * 접수됨 - 증권사에서 주문을 접수함
     */
    ACCEPTED("접수됨"),
    
    /**
     * 부분 체결 - 주문 수량 중 일부만 체결됨
     */
    PARTIALLY_FILLED("부분체결"),
    
    /**
     * 완전 체결 - 주문 수량이 모두 체결됨
     */
    FILLED("체결완료"),
    
    /**
     * 취소됨 - 사용자 또는 시스템에 의해 취소됨
     */
    CANCELLED("취소됨"),
    
    /**
     * 거부됨 - 증권사에서 주문을 거부함
     */
    REJECTED("거부됨"),
    
    /**
     * 실패 - 시스템 오류로 인한 주문 실패
     */
    FAILED("실패");
    
    private final String displayName;
    
    OrderStatus(String displayName) {
        this.displayName = displayName;
    }
    
    public String getDisplayName() {
        return displayName;
    }
    
    /**
     * 활성 상태인지 확인 (아직 완료되지 않은 상태)
     */
    public boolean isActive() {
        return this == PENDING || this == VALIDATING || this == SUBMITTED || 
               this == ACCEPTED || this == PARTIALLY_FILLED;
    }
    
    /**
     * 완료 상태인지 확인 (더 이상 변경되지 않는 상태)
     */
    public boolean isTerminal() {
        return this == FILLED || this == CANCELLED || this == REJECTED || this == FAILED;
    }
    
    /**
     * 체결 관련 상태인지 확인
     */
    public boolean isFilled() {
        return this == PARTIALLY_FILLED || this == FILLED;
    }
    
    /**
     * 실패 관련 상태인지 확인
     */
    public boolean isFailure() {
        return this == REJECTED || this == FAILED;
    }
    
    /**
     * 취소 가능한 상태인지 확인
     */
    public boolean isCancellable() {
        return this == PENDING || this == VALIDATING || this == SUBMITTED || 
               this == ACCEPTED || this == PARTIALLY_FILLED;
    }
    
    /**
     * 다음 상태로 전이 가능한지 검증
     */
    public boolean canTransitionTo(OrderStatus nextStatus) {
        switch (this) {
            case PENDING:
                return nextStatus == VALIDATING || nextStatus == CANCELLED || nextStatus == FAILED;
            case VALIDATING:
                return nextStatus == SUBMITTED || nextStatus == REJECTED || nextStatus == FAILED;
            case SUBMITTED:
                return nextStatus == ACCEPTED || nextStatus == REJECTED || nextStatus == FAILED;
            case ACCEPTED:
                return nextStatus == PARTIALLY_FILLED || nextStatus == FILLED || 
                       nextStatus == CANCELLED || nextStatus == FAILED;
            case PARTIALLY_FILLED:
                return nextStatus == FILLED || nextStatus == CANCELLED;
            default:
                return false; // 터미널 상태에서는 더 이상 전이 불가
        }
    }
}