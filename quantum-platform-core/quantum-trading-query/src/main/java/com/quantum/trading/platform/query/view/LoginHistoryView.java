package com.quantum.trading.platform.query.view;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * 로그인 이력 View Entity
 * 
 * 보안 모니터링을 위한 로그인 성공/실패 이력 저장
 * UserLoginSucceededEvent, UserLoginFailedEvent로부터 생성
 */
@Entity
@Table(name = "login_history_view", indexes = {
    @Index(name = "idx_login_history_user_id", columnList = "user_id"),
    @Index(name = "idx_login_history_username", columnList = "username"),
    @Index(name = "idx_login_history_attempt_time", columnList = "attempt_time"),
    @Index(name = "idx_login_history_success", columnList = "success"),
    @Index(name = "idx_login_history_ip", columnList = "ip_address")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LoginHistoryView {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "user_id", length = 50)
    private String userId;
    
    @Column(name = "username", nullable = false, length = 50)
    private String username;
    
    @Column(name = "success", nullable = false)
    private Boolean success;
    
    @Column(name = "attempt_time", nullable = false)
    private Instant attemptTime;
    
    @Column(name = "ip_address", length = 45) // IPv6 지원
    private String ipAddress;
    
    @Column(name = "user_agent", length = 500)
    private String userAgent;
    
    // 실패한 경우의 추가 정보
    @Column(name = "failure_reason", length = 200)
    private String failureReason;
    
    @Column(name = "failed_attempts", nullable = true)
    private Integer failedAttempts;
    
    @Column(name = "account_locked", nullable = false)
    @Builder.Default
    private Boolean accountLocked = false;
    
    // 성공한 경우의 추가 정보
    @Column(name = "session_id", length = 100)
    private String sessionId;
    
    @Column(name = "previous_login_time")
    private Instant previousLoginTime;
    
    /**
     * 로그인 성공 이력 생성
     */
    public static LoginHistoryView createSuccessHistory(String userId, String username, String sessionId,
                                                       String ipAddress, String userAgent, 
                                                       Instant loginTime, Instant previousLoginTime) {
        return LoginHistoryView.builder()
                .userId(userId)
                .username(username)
                .success(true)
                .attemptTime(loginTime)
                .ipAddress(ipAddress)
                .userAgent(userAgent)
                .sessionId(sessionId)
                .previousLoginTime(previousLoginTime)
                .accountLocked(false)
                .build();
    }
    
    /**
     * 로그인 실패 이력 생성
     */
    public static LoginHistoryView createFailureHistory(String userId, String username, String reason,
                                                       String ipAddress, String userAgent, 
                                                       Instant attemptTime, Integer failedAttempts, 
                                                       boolean accountLocked) {
        return LoginHistoryView.builder()
                .userId(userId)
                .username(username)
                .success(false)
                .attemptTime(attemptTime)
                .ipAddress(ipAddress)
                .userAgent(userAgent)
                .failureReason(reason)
                .failedAttempts(failedAttempts)
                .accountLocked(accountLocked)
                .build();
    }
    
    /**
     * 실패 여부 확인
     */
    public boolean isFailure() {
        return !success;
    }
    
    /**
     * 성공 여부 확인
     */
    public boolean isSuccess() {
        return success;
    }
}