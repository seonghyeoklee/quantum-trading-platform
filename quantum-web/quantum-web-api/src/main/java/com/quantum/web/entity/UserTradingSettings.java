package com.quantum.web.entity;

import com.quantum.web.dto.TradingConfigDto;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 사용자별 트레이딩 설정 엔티티
 */
@Entity
@Table(name = "user_trading_settings")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserTradingSettings {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false, unique = true)
    private String userId;

    @Enumerated(EnumType.STRING)
    @Column(name = "trading_mode", nullable = false)
    private TradingConfigDto.TradingMode tradingMode = TradingConfigDto.TradingMode.SANDBOX;

    @Column(name = "kiwoom_account_id", length = 50)
    private String kiwoomAccountId;

    @Column(name = "max_daily_amount", precision = 15, scale = 2)
    private BigDecimal maxDailyAmount = new BigDecimal("1000000.00");

    @Enumerated(EnumType.STRING)
    @Column(name = "risk_level", nullable = false)
    private TradingConfigDto.RiskLevel riskLevel = TradingConfigDto.RiskLevel.MEDIUM;

    @Column(name = "auto_trading_enabled", nullable = false)
    private boolean autoTradingEnabled = false;

    @Column(name = "notifications_enabled", nullable = false)
    private boolean notificationsEnabled = true;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * DTO로 변환
     */
    public TradingConfigDto.UserTradingSettingsResponse toDto() {
        return TradingConfigDto.UserTradingSettingsResponse.builder()
                .id(this.id)
                .userId(this.userId)
                .tradingMode(this.tradingMode)
                .kiwoomAccountId(this.kiwoomAccountId)
                .maxDailyAmount(this.maxDailyAmount)
                .riskLevel(this.riskLevel)
                .autoTradingEnabled(this.autoTradingEnabled)
                .notificationsEnabled(this.notificationsEnabled)
                .createdAt(this.createdAt)
                .updatedAt(this.updatedAt)
                .build();
    }

    /**
     * 업데이트 요청으로부터 엔티티 업데이트
     */
    public void updateFromRequest(TradingConfigDto.UserTradingSettingsUpdateRequest request) {
        if (request.getTradingMode() != null) {
            this.tradingMode = request.getTradingMode();
        }
        if (request.getKiwoomAccountId() != null) {
            this.kiwoomAccountId = request.getKiwoomAccountId();
        }
        if (request.getMaxDailyAmount() != null) {
            this.maxDailyAmount = request.getMaxDailyAmount();
        }
        if (request.getRiskLevel() != null) {
            this.riskLevel = request.getRiskLevel();
        }
        if (request.getAutoTradingEnabled() != null) {
            this.autoTradingEnabled = request.getAutoTradingEnabled();
        }
        if (request.getNotificationsEnabled() != null) {
            this.notificationsEnabled = request.getNotificationsEnabled();
        }
    }
}