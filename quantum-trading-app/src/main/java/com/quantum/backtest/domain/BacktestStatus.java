package com.quantum.backtest.domain;

/**
 * 백테스팅 실행 상태
 */
public enum BacktestStatus {
    PENDING("대기중", "백테스팅 실행 대기 상태"),
    RUNNING("실행중", "백테스팅 진행 중"),
    COMPLETED("완료", "백테스팅 성공적으로 완료"),
    FAILED("실패", "백테스팅 실행 실패"),
    CANCELLED("취소", "사용자에 의해 취소됨");

    private final String displayName;
    private final String description;

    BacktestStatus(String displayName, String description) {
        this.displayName = displayName;
        this.description = description;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getDescription() {
        return description;
    }

    /**
     * 실행 가능한 상태인지 확인
     */
    public boolean canStart() {
        return this == PENDING;
    }

    /**
     * 취소 가능한 상태인지 확인
     */
    public boolean canCancel() {
        return this == PENDING || this == RUNNING;
    }

    /**
     * 완료된 상태인지 확인
     */
    public boolean isFinished() {
        return this == COMPLETED || this == FAILED || this == CANCELLED;
    }
}