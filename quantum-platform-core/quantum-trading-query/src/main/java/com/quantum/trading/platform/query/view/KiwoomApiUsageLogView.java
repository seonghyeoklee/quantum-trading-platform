package com.quantum.trading.platform.query.view;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

/**
 * 키움증권 API 사용 로그 조회용 View Entity
 * 
 * CQRS Query Side - API 사용 통계 및 모니터링을 위한 로그 테이블
 * Event Handler에서 API 사용 이벤트를 구독하여 로그 생성
 */
@Entity
@Table(name = "kiwoom_api_usage_log_view", indexes = {
    @Index(name = "idx_api_log_user_id", columnList = "user_id"),
    @Index(name = "idx_api_log_kiwoom_account", columnList = "kiwoom_account_id"),
    @Index(name = "idx_api_log_endpoint", columnList = "api_endpoint"),
    @Index(name = "idx_api_log_timestamp", columnList = "usage_timestamp"),
    @Index(name = "idx_api_log_success", columnList = "success"),
    @Index(name = "idx_api_log_user_timestamp", columnList = "user_id,usage_timestamp")
})
@Getter
@Setter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class KiwoomApiUsageLogView {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "log_id")
    private Long logId;

    @Column(name = "user_id", length = 100, nullable = false)
    private String userId;

    @Column(name = "kiwoom_account_id", length = 8, nullable = false)
    private String kiwoomAccountId;

    @Column(name = "api_endpoint", length = 200, nullable = false)
    private String apiEndpoint;

    @Column(name = "request_size", nullable = false)
    private Long requestSize;

    @Column(name = "success", nullable = false)
    private Boolean success;

    @Column(name = "usage_timestamp", nullable = false)
    private Instant usageTimestamp;

    @Column(name = "response_time_ms")
    private Long responseTimeMs;

    @Column(name = "error_message", length = 1000)
    private String errorMessage;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = Instant.now();
    }

    // Factory methods
    public static KiwoomApiUsageLogView create(
            String userId,
            String kiwoomAccountId,
            String apiEndpoint,
            Long requestSize,
            Boolean success,
            Instant usageTimestamp
    ) {
        KiwoomApiUsageLogView view = new KiwoomApiUsageLogView();
        view.userId = userId;
        view.kiwoomAccountId = kiwoomAccountId;
        view.apiEndpoint = apiEndpoint;
        view.requestSize = requestSize;
        view.success = success;
        view.usageTimestamp = usageTimestamp;
        return view;
    }

    // Business methods
    public void setResponseInfo(Long responseTimeMs, String errorMessage) {
        this.responseTimeMs = responseTimeMs;
        this.errorMessage = errorMessage;
    }

    public boolean isSuccessful() {
        return Boolean.TRUE.equals(this.success);
    }

    public boolean isRecentUsage(Instant threshold) {
        return this.usageTimestamp.isAfter(threshold);
    }
}