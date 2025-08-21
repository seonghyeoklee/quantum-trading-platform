package com.quantum.trading.platform.shared.value;

/**
 * 사용자 계정 상태
 * 
 * 사용자 계정의 현재 상태를 나타내는 열거형
 */
public enum UserStatus {
    /**
     * 활성 상태 - 정상적으로 로그인 가능
     */
    ACTIVE,
    
    /**
     * 비활성 상태 - 관리자에 의해 비활성화됨
     */
    INACTIVE,
    
    /**
     * 잠금 상태 - 보안상의 이유로 잠김
     */
    LOCKED,
    
    /**
     * 대기 상태 - 이메일 인증 등 대기 중
     */
    PENDING,
    
    /**
     * 삭제 상태 - 삭제된 계정 (물리적 삭제 전 논리적 삭제)
     */
    DELETED;
    
    /**
     * 로그인이 가능한 상태인지 확인
     */
    public boolean canLogin() {
        return this == ACTIVE;
    }
    
    /**
     * 계정이 활성 상태인지 확인
     */
    public boolean isActive() {
        return this == ACTIVE;
    }
    
    /**
     * 계정이 잠긴 상태인지 확인
     */
    public boolean isLocked() {
        return this == LOCKED;
    }
}