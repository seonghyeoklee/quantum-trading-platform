package com.quantum.trading.platform.query.projection;

import com.quantum.trading.platform.query.repository.LoginHistoryViewRepository;
import com.quantum.trading.platform.query.view.LoginHistoryView;
import com.quantum.trading.platform.shared.event.UserLoginFailedEvent;
import com.quantum.trading.platform.shared.event.UserLoginSucceededEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

/**
 * 로그인 이력 Projection Handler
 * 
 * 로그인 관련 이벤트를 LoginHistoryView로 변환하여 저장
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class LoginHistoryProjectionHandler {
    
    private final LoginHistoryViewRepository loginHistoryRepository;
    
    /**
     * 로그인 성공 이벤트 처리
     */
    @EventHandler
    public void on(UserLoginSucceededEvent event) {
        log.info("Processing UserLoginSucceededEvent for user: {}", event.getUsername());
        
        try {
            LoginHistoryView loginHistory = LoginHistoryView.createSuccessHistory(
                event.getUserId().getValue(),
                event.getUsername(),
                event.getSessionId(),
                event.getIpAddress(),
                event.getUserAgent(),
                event.getLoginTime(),
                event.getPreviousLoginTime()
            );
            
            LoginHistoryView saved = loginHistoryRepository.save(loginHistory);
            log.debug("Login success history saved with ID: {} for user: {}", 
                     saved.getId(), event.getUsername());
            
        } catch (Exception e) {
            log.error("Failed to save login success history for user: {}", event.getUsername(), e);
        }
    }
    
    /**
     * 로그인 실패 이벤트 처리
     */
    @EventHandler
    public void on(UserLoginFailedEvent event) {
        log.info("Processing UserLoginFailedEvent for user: {} (attempts: {})", 
                event.getUsername(), event.getFailedAttempts());
        
        try {
            LoginHistoryView loginHistory = LoginHistoryView.createFailureHistory(
                event.getUserId() != null ? event.getUserId().getValue() : null,
                event.getUsername(),
                event.getReason(),
                event.getIpAddress(),
                event.getUserAgent(),
                event.getAttemptTime(),
                event.getFailedAttempts(),
                event.isAccountLocked()
            );
            
            LoginHistoryView saved = loginHistoryRepository.save(loginHistory);
            log.debug("Login failure history saved with ID: {} for user: {} (reason: {})", 
                     saved.getId(), event.getUsername(), event.getReason());
            
            // 계정 잠금된 경우 경고 로그
            if (event.isAccountLocked()) {
                log.warn("Account locked for user: {} after {} failed attempts", 
                        event.getUsername(), event.getFailedAttempts());
            }
            
        } catch (Exception e) {
            log.error("Failed to save login failure history for user: {}", event.getUsername(), e);
        }
    }
}