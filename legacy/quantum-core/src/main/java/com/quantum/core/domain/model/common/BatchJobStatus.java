package com.quantum.core.domain.model.common;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * 배치 Job 상태 코드 열거형
 * Spring Batch Job 상태를 타입 안전하게 관리
 */
@Getter
@RequiredArgsConstructor
public enum BatchJobStatus {

    PENDING("PENDING", "대기중", "Job이 실행 대기 중입니다"),
    RUNNING("RUNNING", "실행중", "Job이 현재 실행 중입니다"),
    COMPLETED("COMPLETED", "완료", "Job이 성공적으로 완료되었습니다"),
    FAILED("FAILED", "실패", "Job 실행 중 오류가 발생했습니다"),
    STOPPED("STOPPED", "중지", "Job이 중지되었습니다"),
    UNKNOWN("UNKNOWN", "알수없음", "Job 상태를 확인할 수 없습니다"),
    
    // 에러 상태
    ALREADY_RUNNING("JOB_ALREADY_RUNNING", "이미실행중", "동일한 Job이 이미 실행 중입니다"),
    ALREADY_COMPLETED("JOB_ALREADY_COMPLETED", "이미완료", "동일한 파라미터로 이미 완료된 Job이 있습니다"),
    START_FAILED("JOB_START_FAILED", "시작실패", "Job 시작에 실패했습니다"),
    NEVER_EXECUTED("NEVER_EXECUTED", "미실행", "아직 실행된 적이 없습니다"),
    NO_EXECUTIONS("NO_EXECUTIONS", "실행기록없음", "실행 기록이 없습니다");

    private final String code;
    private final String koreanName;
    private final String description;

    public static BatchJobStatus fromCode(String code) {
        if (code == null || code.trim().isEmpty()) {
            return UNKNOWN;
        }
        
        for (BatchJobStatus status : values()) {
            if (status.code.equalsIgnoreCase(code.trim())) {
                return status;
            }
        }
        
        return UNKNOWN;
    }

    public boolean isTerminated() {
        return this == COMPLETED || this == FAILED || this == STOPPED;
    }

    public boolean isActive() {
        return this == RUNNING || this == PENDING;
    }

    public boolean isError() {
        return this == FAILED || this == START_FAILED || this == ALREADY_RUNNING;
    }
}