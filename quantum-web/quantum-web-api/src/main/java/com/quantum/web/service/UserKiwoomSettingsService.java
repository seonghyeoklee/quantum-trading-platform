package com.quantum.web.service;

import com.quantum.trading.platform.query.view.UserKiwoomSettingsView;
import com.quantum.trading.platform.query.repository.UserKiwoomSettingsViewRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * 사용자별 키움증권 설정 관리 서비스
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class UserKiwoomSettingsService {

    private final UserKiwoomSettingsViewRepository userKiwoomSettingsRepository;
    private final KiwoomTokenService kiwoomTokenService;

    /**
     * 사용자 설정 조회 (없으면 기본값으로 생성)
     */
    @Transactional
    public UserKiwoomSettingsView getUserSettings(String userId) {
        log.debug("Getting Kiwoom settings for user: {}", userId);
        
        Optional<UserKiwoomSettingsView> settingsOpt = userKiwoomSettingsRepository.findByUserId(userId);
        
        if (settingsOpt.isPresent()) {
            log.debug("Found existing settings for user: {}", userId);
            return settingsOpt.get();
        }
        
        // 설정이 없으면 기본값으로 생성
        log.info("Creating default Kiwoom settings for user: {}", userId);
        UserKiwoomSettingsView defaultSettings = UserKiwoomSettingsView.createDefault(userId);
        return userKiwoomSettingsRepository.save(defaultSettings);
    }

    /**
     * 사용자의 현재 기본 거래 모드 조회
     */
    public boolean getUserDefaultRealMode(String userId) {
        UserKiwoomSettingsView settings = getUserSettings(userId);
        boolean isRealMode = settings.isDefaultRealMode();
        
        log.debug("User {} default trading mode: {}", userId, isRealMode ? "real" : "sandbox");
        return isRealMode;
    }

    /**
     * 사용자 거래 모드 전환 (sandbox ↔ real)
     */
    @Transactional
    public UserKiwoomSettingsView switchTradingMode(String userId, boolean newRealMode) {
        try {
            log.info("🔄 Switching trading mode for user: {} to {}", 
                    userId, newRealMode ? "real" : "sandbox");

            UserKiwoomSettingsView settings = getUserSettings(userId);
            boolean oldRealMode = settings.isDefaultRealMode();

            if (oldRealMode == newRealMode) {
                log.debug("User {} already in {} mode, no change needed", 
                        userId, newRealMode ? "real" : "sandbox");
                return settings;
            }

            // 모드 전환
            if (newRealMode) {
                settings.switchToRealMode();
            } else {
                settings.switchToSandboxMode();
            }

            settings = userKiwoomSettingsRepository.save(settings);

            // 자동 토큰 재발급이 활성화된 경우 새 토큰 발급
            if (settings.isAutoReissueOnModeSwitch()) {
                try {
                    log.info("Auto reissuing token for user {} in {} mode", 
                            userId, newRealMode ? "real" : "sandbox");
                    kiwoomTokenService.issueKiwoomToken(userId, newRealMode);
                } catch (Exception e) {
                    log.warn("Failed to auto-reissue token for user {} after mode switch: {}", 
                            userId, e.getMessage());
                    // 토큰 발급 실패는 설정 변경을 롤백하지 않음 (사용자가 수동으로 재발급 가능)
                }
            }

            log.info("✅ Successfully switched user {} from {} to {} mode", 
                    userId, oldRealMode ? "real" : "sandbox", newRealMode ? "real" : "sandbox");

            return settings;

        } catch (Exception e) {
            log.error("❌ Failed to switch trading mode for user: {}", userId, e);
            throw new UserSettingsException("Failed to switch trading mode", e);
        }
    }

    /**
     * 토큰 만료 알림 설정 업데이트
     */
    @Transactional
    public UserKiwoomSettingsView updateTokenExpiryNotification(String userId, boolean enabled, Integer thresholdMinutes) {
        try {
            log.info("Updating token expiry notification for user: {} - enabled: {}, threshold: {}min", 
                    userId, enabled, thresholdMinutes);

            UserKiwoomSettingsView settings = getUserSettings(userId);
            
            settings.updateTokenExpiryNotification(enabled);
            
            if (enabled && thresholdMinutes != null) {
                settings.updateNotificationThreshold(thresholdMinutes);
            }

            settings = userKiwoomSettingsRepository.save(settings);
            log.info("✅ Updated token expiry notification settings for user: {}", userId);

            return settings;

        } catch (Exception e) {
            log.error("❌ Failed to update token expiry notification for user: {}", userId, e);
            throw new UserSettingsException("Failed to update notification settings", e);
        }
    }

    /**
     * 자동 토큰 갱신 설정 업데이트
     */
    @Transactional
    public UserKiwoomSettingsView updateAutoRefreshSetting(String userId, boolean enabled) {
        try {
            log.info("Updating auto refresh setting for user: {} - enabled: {}", userId, enabled);

            UserKiwoomSettingsView settings = getUserSettings(userId);
            settings.updateAutoRefreshSetting(enabled);

            settings = userKiwoomSettingsRepository.save(settings);
            log.info("✅ Updated auto refresh setting for user: {}", userId);

            return settings;

        } catch (Exception e) {
            log.error("❌ Failed to update auto refresh setting for user: {}", userId, e);
            throw new UserSettingsException("Failed to update auto refresh setting", e);
        }
    }

    /**
     * 모드 전환 시 자동 재발급 설정 업데이트
     */
    @Transactional
    public UserKiwoomSettingsView updateAutoReissueSetting(String userId, boolean enabled) {
        try {
            log.info("Updating auto reissue setting for user: {} - enabled: {}", userId, enabled);

            UserKiwoomSettingsView settings = getUserSettings(userId);
            settings.updateAutoReissueSetting(enabled);

            settings = userKiwoomSettingsRepository.save(settings);
            log.info("✅ Updated auto reissue setting for user: {}", userId);

            return settings;

        } catch (Exception e) {
            log.error("❌ Failed to update auto reissue setting for user: {}", userId, e);
            throw new UserSettingsException("Failed to update auto reissue setting", e);
        }
    }

    /**
     * 사용자 설정 전체 업데이트
     */
    @Transactional
    public UserKiwoomSettingsView updateUserSettings(String userId, UserSettingsUpdateRequest request) {
        try {
            log.info("Updating user settings for user: {}", userId);

            UserKiwoomSettingsView settings = getUserSettings(userId);

            // 거래 모드 변경이 있는 경우
            if (request.getDefaultRealMode() != null && 
                !request.getDefaultRealMode().equals(settings.isDefaultRealMode())) {
                return switchTradingMode(userId, request.getDefaultRealMode());
            }

            // 기타 설정 업데이트
            if (request.getAutoRefreshEnabled() != null) {
                settings.updateAutoRefreshSetting(request.getAutoRefreshEnabled());
            }

            if (request.getTokenExpiryNotification() != null) {
                settings.updateTokenExpiryNotification(request.getTokenExpiryNotification());
            }

            if (request.getNotificationThresholdMinutes() != null) {
                settings.updateNotificationThreshold(request.getNotificationThresholdMinutes());
            }

            if (request.getAutoReissueOnModeSwitch() != null) {
                settings.updateAutoReissueSetting(request.getAutoReissueOnModeSwitch());
            }

            settings = userKiwoomSettingsRepository.save(settings);
            log.info("✅ Updated user settings for user: {}", userId);

            return settings;

        } catch (Exception e) {
            log.error("❌ Failed to update user settings for user: {}", userId, e);
            throw new UserSettingsException("Failed to update user settings", e);
        }
    }

    /**
     * 사용자 설정 삭제
     */
    @Transactional
    public void deleteUserSettings(String userId) {
        try {
            log.info("Deleting user settings for user: {}", userId);

            if (userKiwoomSettingsRepository.existsByUserId(userId)) {
                userKiwoomSettingsRepository.deleteByUserId(userId);
                log.info("✅ Deleted user settings for user: {}", userId);
            } else {
                log.debug("No settings found to delete for user: {}", userId);
            }

        } catch (Exception e) {
            log.error("❌ Failed to delete user settings for user: {}", userId, e);
            throw new UserSettingsException("Failed to delete user settings", e);
        }
    }

    /**
     * 모든 사용자 설정 통계 조회
     */
    public UserSettingsStatistics getUserSettingsStatistics() {
        try {
            Object[] stats = userKiwoomSettingsRepository.getSettingsStatistics();
            
            if (stats != null && stats.length > 0) {
                Object[] row = stats;
                return UserSettingsStatistics.builder()
                        .totalUsers(((Number) row[0]).longValue())
                        .realModeUsers(((Number) row[1]).longValue())
                        .sandboxModeUsers(((Number) row[2]).longValue())
                        .autoRefreshUsers(((Number) row[3]).longValue())
                        .notificationUsers(((Number) row[4]).longValue())
                        .build();
            }

            return UserSettingsStatistics.builder().build();

        } catch (Exception e) {
            log.error("Failed to get user settings statistics", e);
            return UserSettingsStatistics.builder().build();
        }
    }

    /**
     * 최근 모드 변경 사용자들 조회
     */
    public List<UserKiwoomSettingsView> getRecentModeChanges(int hours) {
        Instant since = Instant.now().minusSeconds(hours * 3600L);
        return userKiwoomSettingsRepository.findRecentModeChanges(since);
    }

    // Inner classes

    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class UserSettingsUpdateRequest {
        private Boolean defaultRealMode;
        private Boolean autoRefreshEnabled;
        private Boolean tokenExpiryNotification;
        private Integer notificationThresholdMinutes;
        private Boolean autoReissueOnModeSwitch;
    }

    @lombok.Data
    @lombok.Builder
    public static class UserSettingsStatistics {
        @lombok.Builder.Default
        private long totalUsers = 0;
        @lombok.Builder.Default
        private long realModeUsers = 0;
        @lombok.Builder.Default
        private long sandboxModeUsers = 0;
        @lombok.Builder.Default
        private long autoRefreshUsers = 0;
        @lombok.Builder.Default
        private long notificationUsers = 0;

        public double getRealModePercentage() {
            return totalUsers > 0 ? (realModeUsers * 100.0 / totalUsers) : 0.0;
        }

        public double getSandboxModePercentage() {
            return totalUsers > 0 ? (sandboxModeUsers * 100.0 / totalUsers) : 0.0;
        }
    }

    /**
     * 사용자 설정 관련 예외
     */
    public static class UserSettingsException extends RuntimeException {
        public UserSettingsException(String message) {
            super(message);
        }

        public UserSettingsException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}