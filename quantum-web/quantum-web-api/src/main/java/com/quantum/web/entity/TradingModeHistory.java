package com.quantum.web.entity;

import com.quantum.web.dto.TradingConfigDto;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/**
 * 트레이딩 모드 변경 이력 엔티티
 */
@Entity
@Table(name = "trading_mode_history")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TradingModeHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Enumerated(EnumType.STRING)
    @Column(name = "previous_mode")
    private TradingConfigDto.TradingMode previousMode;

    @Enumerated(EnumType.STRING)
    @Column(name = "new_mode", nullable = false)
    private TradingConfigDto.TradingMode newMode;

    @Column(name = "changed_by", nullable = false)
    private String changedBy;

    @Column(name = "change_reason", columnDefinition = "TEXT")
    private String changeReason;

    @Column(name = "ip_address", length = 45)
    private String ipAddress;

    @Column(name = "user_agent", columnDefinition = "TEXT")
    private String userAgent;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
    }

    /**
     * DTO로 변환
     */
    public TradingConfigDto.TradingModeHistoryResponse toDto() {
        return TradingConfigDto.TradingModeHistoryResponse.builder()
                .id(this.id)
                .userId(this.userId)
                .previousMode(this.previousMode)
                .newMode(this.newMode)
                .changedBy(this.changedBy)
                .changeReason(this.changeReason)
                .ipAddress(this.ipAddress)
                .userAgent(this.userAgent)
                .createdAt(this.createdAt)
                .build();
    }
}