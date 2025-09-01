package com.quantum.trading.platform.query.view;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.extern.slf4j.Slf4j;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import java.time.Instant;

/**
 * 사용자별 키움증권 설정 뷰
 * 
 * 사용자가 선택한 키움증권 기본 모드(sandbox/real)와 관련 설정을 관리
 */
@Entity
@Table(name = "user_kiwoom_settings")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Slf4j
public class UserKiwoomSettingsView {

    @Id
    @Column(name = "user_id", nullable = false, length = 100)
    private String userId;

    /**
     * 기본 거래 모드 (true: 실전투자, false: 모의투자/sandbox)
     */
    @Column(name = "default_real_mode", nullable = false)
    @Builder.Default
    private boolean defaultRealMode = false;

    /**
     * 자동 토큰 갱신 활성화 여부
     */
    @Column(name = "auto_refresh_enabled", nullable = false)
    @Builder.Default
    private boolean autoRefreshEnabled = true;

    /**
     * 토큰 만료 알림 활성화 여부
     */
    @Column(name = "token_expiry_notification", nullable = false)
    @Builder.Default
    private boolean tokenExpiryNotification = true;

    /**
     * 토큰 만료 알림 임계시간 (분)
     */
    @Column(name = "notification_threshold_minutes", nullable = false)
    @Builder.Default
    private int notificationThresholdMinutes = 30;

    /**
     * 모드 전환 시 자동 토큰 재발급 여부
     */
    @Column(name = "auto_reissue_on_mode_switch", nullable = false)
    @Builder.Default
    private boolean autoReissueOnModeSwitch = true;

    /**
     * 설정 생성 시각
     */
    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    /**
     * 설정 수정 시각
     */
    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    /**
     * 최근 모드 변경 시각
     */
    @Column(name = "last_mode_change_at")
    private Instant lastModeChangeAt;

    /**
     * 설정 버전 (낙관적 잠금)
     */
    @Column(name = "version", nullable = false)
    @Builder.Default
    private Long version = 1L;

    @PrePersist
    public void prePersist() {
        Instant now = Instant.now();
        this.createdAt = now;
        this.updatedAt = now;
        this.version = 1L;
        
        log.debug("Creating UserKiwoomSettings for user: {}, default mode: {}", 
                userId, defaultRealMode ? "real" : "sandbox");
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = Instant.now();
        this.version++;
        
        log.debug("Updating UserKiwoomSettings for user: {}, version: {}", userId, version);
    }

    // ===== 비즈니스 메서드 =====

    /**
     * 기본 모드를 실전투자로 변경
     */
    public void switchToRealMode() {
        if (!this.defaultRealMode) {
            this.defaultRealMode = true;
            this.lastModeChangeAt = Instant.now();
            log.info("User {} switched to real trading mode", userId);
        }
    }

    /**
     * 기본 모드를 모의투자로 변경
     */
    public void switchToSandboxMode() {
        if (this.defaultRealMode) {
            this.defaultRealMode = false;
            this.lastModeChangeAt = Instant.now();
            log.info("User {} switched to sandbox trading mode", userId);
        }
    }

    /**
     * 토큰 만료 알림 임계시간 업데이트
     */
    public void updateNotificationThreshold(int minutes) {
        if (minutes < 5 || minutes > 1440) { // 5분 ~ 24시간
            throw new IllegalArgumentException("Notification threshold must be between 5 and 1440 minutes");
        }
        this.notificationThresholdMinutes = minutes;
        log.debug("Updated notification threshold for user {}: {} minutes", userId, minutes);
    }

    /**
     * 자동 토큰 갱신 설정 업데이트
     */
    public void updateAutoRefreshSetting(boolean enabled) {
        this.autoRefreshEnabled = enabled;
        log.debug("Updated auto refresh setting for user {}: {}", userId, enabled);
    }

    /**
     * 모드 전환 시 자동 재발급 설정 업데이트
     */
    public void updateAutoReissueSetting(boolean enabled) {
        this.autoReissueOnModeSwitch = enabled;
        log.debug("Updated auto reissue on mode switch for user {}: {}", userId, enabled);
    }

    /**
     * 토큰 만료 알림 설정 업데이트
     */
    public void updateTokenExpiryNotification(boolean enabled) {
        this.tokenExpiryNotification = enabled;
        log.debug("Updated token expiry notification for user {}: {}", userId, enabled);
    }

    /**
     * 설정이 최근에 변경되었는지 확인 (1시간 이내)
     */
    public boolean isRecentlyModified() {
        if (lastModeChangeAt == null) return false;
        return lastModeChangeAt.isAfter(Instant.now().minusSeconds(3600));
    }

    /**
     * 현재 모드 문자열 반환
     */
    public String getCurrentModeString() {
        return defaultRealMode ? "real" : "sandbox";
    }

    /**
     * 설정 요약 정보
     */
    public String getSettingsSummary() {
        return String.format(
            "UserKiwoomSettings[user=%s, mode=%s, autoRefresh=%s, notification=%s, threshold=%dm]",
            userId,
            getCurrentModeString(),
            autoRefreshEnabled,
            tokenExpiryNotification,
            notificationThresholdMinutes
        );
    }

    // ===== Static Factory Methods =====

    /**
     * 새로운 사용자를 위한 기본 설정 생성
     */
    public static UserKiwoomSettingsView createDefault(String userId) {
        return UserKiwoomSettingsView.builder()
                .userId(userId)
                .defaultRealMode(false) // 기본값: sandbox 모드
                .autoRefreshEnabled(true)
                .tokenExpiryNotification(true)
                .notificationThresholdMinutes(30)
                .autoReissueOnModeSwitch(true)
                .build();
    }

    /**
     * 실전투자 사용자를 위한 설정 생성
     */
    public static UserKiwoomSettingsView createForRealTrading(String userId) {
        return UserKiwoomSettingsView.builder()
                .userId(userId)
                .defaultRealMode(true) // 실전투자 모드
                .autoRefreshEnabled(true)
                .tokenExpiryNotification(true)
                .notificationThresholdMinutes(15) // 더 짧은 알림 시간
                .autoReissueOnModeSwitch(true)
                .build();
    }
}