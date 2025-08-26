package com.quantum.trading.platform.query.projection;

import com.quantum.trading.platform.query.repository.UserViewRepository;
import com.quantum.trading.platform.query.view.UserView;
import com.quantum.trading.platform.shared.event.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;

/**
 * User Projection Handler
 * 
 * Domain Events를 구독하여 UserView Read Model을 업데이트
 * Event Sourcing의 Query Side 역할 수행
 */
@Component
@RequiredArgsConstructor
@Slf4j
@Transactional
public class UserProjectionHandler {
    
    private final UserViewRepository userViewRepository;
    
    /**
     * 사용자 등록 이벤트 처리
     */
    @EventHandler
    public void on(UserRegisteredEvent event) {
        log.info("Processing UserRegisteredEvent for user: {}", event.getUsername());
        
        try {
            // 중복 체크
            if (userViewRepository.existsByUsername(event.getUsername())) {
                log.warn("User already exists with username: {}", event.getUsername());
                return;
            }
            
            if (userViewRepository.existsByEmail(event.getEmail())) {
                log.warn("User already exists with email: {}", event.getEmail());
                return;
            }
            
            // UserView 생성 및 저장
            UserView userView = UserView.fromUserRegistered(
                    event.getUserId().getValue(),
                    event.getUsername(),
                    event.getPasswordHash(),
                    event.getName(),
                    event.getEmail(),
                    event.getPhone(),
                    event.getInitialRoles(),
                    event.getRegisteredAt(),
                    event.getRegisteredBy()
            );
            
            userViewRepository.save(userView);
            
            log.info("UserView created successfully for user: {} with ID: {}", 
                    event.getUsername(), event.getUserId().getValue());
            
        } catch (Exception e) {
            log.error("Failed to process UserRegisteredEvent for user: {}", event.getUsername(), e);
            throw e;
        }
    }
    
    /**
     * 로그인 성공 이벤트 처리
     */
    @EventHandler
    public void on(UserLoginSucceededEvent event) {
        log.info("Processing UserLoginSucceededEvent for user: {}", event.getUsername());
        
        try {
            UserView userView = userViewRepository.findById(event.getUserId().getValue())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for login success: " + event.getUserId().getValue()));
            
            userView.updateOnLoginSuccess(event.getSessionId(), event.getLoginTime());
            userViewRepository.save(userView);
            
            log.info("UserView updated for successful login: {} with session: {}", 
                    event.getUsername(), event.getSessionId());
            
        } catch (Exception e) {
            log.error("Failed to process UserLoginSucceededEvent for user: {}", event.getUsername(), e);
            throw e;
        }
    }
    
    /**
     * 로그인 실패 이벤트 처리
     */
    @EventHandler
    public void on(UserLoginFailedEvent event) {
        log.info("Processing UserLoginFailedEvent for user: {} (attempt: {})", 
                event.getUsername(), event.getFailedAttempts());
        
        try {
            UserView userView = userViewRepository.findById(event.getUserId().getValue())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for login failure: " + event.getUserId().getValue()));
            
            userView.updateOnLoginFailure(event.getFailedAttempts(), event.isAccountLocked());
            userViewRepository.save(userView);
            
            if (event.isAccountLocked()) {
                log.warn("UserView updated - account locked for user: {} after {} failed attempts", 
                        event.getUsername(), event.getFailedAttempts());
            } else {
                log.info("UserView updated for failed login: {} (attempt: {})", 
                        event.getUsername(), event.getFailedAttempts());
            }
            
        } catch (Exception e) {
            log.error("Failed to process UserLoginFailedEvent for user: {}", event.getUsername(), e);
            throw e;
        }
    }
    
    /**
     * 로그아웃 이벤트 처리
     */
    @EventHandler
    public void on(UserLoggedOutEvent event) {
        log.info("Processing UserLoggedOutEvent for user: {} (session: {})", 
                event.getUsername(), event.getSessionId());
        
        try {
            UserView userView = userViewRepository.findById(event.getUserId().getValue())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for logout: " + event.getUserId().getValue()));
            
            userView.clearSession();
            userViewRepository.save(userView);
            
            log.info("UserView updated for logout: {} - session cleared", event.getUsername());
            
        } catch (Exception e) {
            log.error("Failed to process UserLoggedOutEvent for user: {}", event.getUsername(), e);
            throw e;
        }
    }
    
    /**
     * 사용자 권한 부여 이벤트 처리
     */
    @EventHandler
    public void on(UserRoleGrantedEvent event) {
        log.info("Processing UserRoleGrantedEvent for user: {} - role: {}", 
                event.getUsername(), event.getRoleName());
        
        try {
            UserView userView = userViewRepository.findById(event.getUserId().getValue())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for role grant: " + event.getUserId().getValue()));
            
            userView.addRole(event.getRoleName());
            userViewRepository.save(userView);
            
            log.info("UserView updated - role granted: {} to user: {}", 
                    event.getRoleName(), event.getUsername());
            
        } catch (Exception e) {
            log.error("Failed to process UserRoleGrantedEvent for user: {}", event.getUsername(), e);
            throw e;
        }
    }
    
    /**
     * 계정 잠금 이벤트 처리
     */
    @EventHandler
    public void on(UserAccountLockedEvent event) {
        log.info("Processing UserAccountLockedEvent for user: {} - reason: {}", 
                event.getUsername(), event.getReason());
        
        try {
            UserView userView = userViewRepository.findById(event.getUserId().getValue())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for account lock: " + event.getUserId().getValue()));
            
            userView.lockAccount();
            userViewRepository.save(userView);
            
            log.warn("UserView updated - account locked for user: {} - reason: {}", 
                    event.getUsername(), event.getReason());
            
        } catch (Exception e) {
            log.error("Failed to process UserAccountLockedEvent for user: {}", event.getUsername(), e);
            throw e;
        }
    }
    
    /**
     * 2FA 활성화 이벤트 처리
     */
    @EventHandler
    public void on(TwoFactorEnabledEvent event) {
        log.info("Processing TwoFactorEnabledEvent for user: {}", event.userId().getValue());
        
        try {
            UserView userView = userViewRepository.findById(event.userId().getValue())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for 2FA enable: " + event.userId().getValue()));
            
            userView.enableTwoFactor(event.totpSecretKey(), event.backupCodeHashes());
            userViewRepository.save(userView);
            
            log.info("UserView updated - 2FA enabled for user: {} with {} backup codes", 
                    event.userId().getValue(), event.backupCodeHashes().size());
            
        } catch (Exception e) {
            log.error("Failed to process TwoFactorEnabledEvent for user: {}", event.userId().getValue(), e);
            throw e;
        }
    }
    
    /**
     * 2FA 비활성화 이벤트 처리
     */
    @EventHandler
    public void on(TwoFactorDisabledEvent event) {
        log.info("Processing TwoFactorDisabledEvent for user: {} - reason: {}", 
                event.userId().getValue(), event.reason());
        
        try {
            UserView userView = userViewRepository.findById(event.userId().getValue())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for 2FA disable: " + event.userId().getValue()));
            
            userView.disableTwoFactor();
            userViewRepository.save(userView);
            
            log.info("UserView updated - 2FA disabled for user: {} - reason: {}", 
                    event.userId().getValue(), event.reason());
            
        } catch (Exception e) {
            log.error("Failed to process TwoFactorDisabledEvent for user: {}", event.userId().getValue(), e);
            throw e;
        }
    }
    
    /**
     * 백업 코드 사용 이벤트 처리
     */
    @EventHandler
    public void on(BackupCodeUsedEvent event) {
        log.info("Processing BackupCodeUsedEvent for user: {} - remaining codes: {}", 
                event.userId().getValue(), event.remainingBackupCodes());
        
        try {
            UserView userView = userViewRepository.findById(event.userId().getValue())
                    .orElseThrow(() -> new IllegalStateException(
                            "UserView not found for backup code usage: " + event.userId().getValue()));
            
            boolean codeUsed = userView.useBackupCode(event.backupCodeHash());
            if (codeUsed) {
                userViewRepository.save(userView);
                log.info("UserView updated - backup code used for user: {}, remaining codes: {}", 
                        event.userId().getValue(), userView.getRemainingBackupCodesCount());
            } else {
                log.warn("Backup code was not found in UserView for user: {}", event.userId().getValue());
            }
            
        } catch (Exception e) {
            log.error("Failed to process BackupCodeUsedEvent for user: {}", event.userId().getValue(), e);
            throw e;
        }
    }
}