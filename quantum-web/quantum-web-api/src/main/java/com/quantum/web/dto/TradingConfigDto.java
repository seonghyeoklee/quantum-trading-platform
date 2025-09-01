package com.quantum.web.dto;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 트레이딩 설정 관련 DTO 클래스들
 */
public class TradingConfigDto {

    /**
     * 트레이딩 모드 열거형
     */
    public enum TradingMode {
        SANDBOX("SANDBOX"),
        REAL("REAL");

        private final String description;

        TradingMode(String description) {
            this.description = description;
        }

        public String getDescription() {
            return description;
        }
    }

    /**
     * 리스크 레벨 열거형
     */
    public enum RiskLevel {
        LOW("보수적"),
        MEDIUM("중간"),
        HIGH("공격적");

        private final String description;

        RiskLevel(String description) {
            this.description = description;
        }

        public String getDescription() {
            return description;
        }
    }

    /**
     * 사용자 트레이딩 설정 조회 응답
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UserTradingSettingsResponse {
        private Long id;
        private String userId;
        private TradingMode tradingMode;
        private String kiwoomAccountId;
        private BigDecimal maxDailyAmount;
        private RiskLevel riskLevel;
        private boolean autoTradingEnabled;
        private boolean notificationsEnabled;
        private LocalDateTime createdAt;
        private LocalDateTime updatedAt;
    }

    /**
     * 트레이딩 모드 변경 요청
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TradingModeChangeRequest {
        @NotNull(message = "트레이딩 모드는 필수입니다")
        private TradingMode tradingMode;

        private String changeReason;

        @Pattern(regexp = "^\\d{6}$", message = "TOTP 코드는 6자리 숫자여야 합니다")
        private String totpCode; // 실전투자 전환 시 2FA 필요
    }

    /**
     * 사용자 트레이딩 설정 업데이트 요청
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UserTradingSettingsUpdateRequest {
        @NotNull(message = "트레이딩 모드는 필수입니다")
        private TradingMode tradingMode;

        private String kiwoomAccountId;

        @DecimalMin(value = "0.00", message = "최대 투자금액은 0 이상이어야 합니다")
        @DecimalMax(value = "100000000.00", message = "최대 투자금액은 1억원을 초과할 수 없습니다")
        private BigDecimal maxDailyAmount;

        @NotNull(message = "리스크 레벨은 필수입니다")
        private RiskLevel riskLevel;

        private Boolean autoTradingEnabled;
        private Boolean notificationsEnabled;
        private String changeReason;

        @Pattern(regexp = "^\\d{6}$", message = "TOTP 코드는 6자리 숫자여야 합니다")
        private String totpCode; // 실전투자 전환 시 2FA 필요
    }

    /**
     * 시스템 설정 응답
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SystemConfigResponse {
        private String configKey;
        private String configValue;
        private String configType;
        private String description;
        private boolean isEncrypted;
        private LocalDateTime updatedAt;
        private String updatedBy;
    }

    /**
     * 트레이딩 모드 변경 이력 응답
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TradingModeHistoryResponse {
        private Long id;
        private String userId;
        private TradingMode previousMode;
        private TradingMode newMode;
        private String changedBy;
        private String changeReason;
        private String ipAddress;
        private String userAgent;
        private LocalDateTime createdAt;
    }

    /**
     * Python 어댑터 알림 요청
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PythonAdapterNotificationRequest {
        private String userId;
        private boolean sandboxMode;
        private String kiwoomAccountId;
        private LocalDateTime timestamp;
    }

    /**
     * 트레이딩 설정 요약 응답 (대시보드용)
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TradingConfigSummaryResponse {
        private TradingMode currentMode;
        private String modeDescription;
        private boolean isProductionAllowed;
        private boolean requires2FA;
        private BigDecimal maxDailyAmount;
        private RiskLevel riskLevel;
        private boolean autoTradingEnabled;
        private int recentModeChanges; // 최근 24시간 내 모드 변경 횟수
        private LocalDateTime lastModeChange;
        private boolean pythonAdapterConnected;
    }
}