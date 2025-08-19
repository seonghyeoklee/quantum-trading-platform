package com.quantum.core.domain.model.kis;

import com.quantum.core.infrastructure.common.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

import java.time.LocalDateTime;

/**
 * KIS API 토큰 저장 엔티티 - 토큰 재발급 제한(1분당 1회) 대응
 */
@Entity
@Table(name = "tb_kis_token")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Comment("KIS API 액세스 토큰 저장소")
public class KisToken extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "token_type", length = 20, nullable = false)
    @Comment("토큰 타입 (Bearer)")
    private String tokenType;

    @Column(name = "access_token", columnDefinition = "TEXT", nullable = false)
    @Comment("액세스 토큰")
    private String accessToken;

    @Column(name = "expires_at", nullable = false)
    @Comment("토큰 만료 시간")
    private LocalDateTime expiresAt;

    @Column(name = "expires_in", nullable = false)
    @Comment("토큰 유효 시간 (초)")
    private Long expiresIn;

    @Column(name = "is_active", nullable = false)
    @Comment("토큰 활성화 여부")
    private Boolean isActive;

    @Builder
    public KisToken(String tokenType, String accessToken, LocalDateTime expiresAt, Long expiresIn) {
        this.tokenType = tokenType;
        this.accessToken = accessToken;
        this.expiresAt = expiresAt;
        this.expiresIn = expiresIn;
        this.isActive = true;
    }

    /**
     * 토큰 만료 여부 확인 (5분 여유 시간 포함)
     */
    public boolean isExpired() {
        return LocalDateTime.now().isAfter(expiresAt.minusMinutes(5));
    }

    /**
     * 토큰 비활성화
     */
    public void deactivate() {
        this.isActive = false;
    }

    /**
     * KIS API 응답에서 토큰 생성
     */
    public static KisToken fromKisResponse(String tokenType, String accessToken, String expiresAtString, Long expiresIn) {
        // KIS 응답 형식: "2025-08-19 18:29:40"
        LocalDateTime expiresAt = LocalDateTime.parse(expiresAtString.replace(" ", "T"));
        
        return KisToken.builder()
                .tokenType(tokenType)
                .accessToken(accessToken)
                .expiresAt(expiresAt)
                .expiresIn(expiresIn)
                .build();
    }
}