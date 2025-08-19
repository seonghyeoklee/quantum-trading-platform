package com.quantum.api.kiwoom.dto.auth;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * Redis에 캐시되는 토큰 정보
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class CachedTokenInfo {
    
    private String appkey;              // 앱키
    private String token;               // 접근토큰
    private LocalDateTime issuedAt;     // 발급시간
    private LocalDateTime expiresAt;    // 만료시간 (발급 + 24시간)
    private String expiresDt;           // 키움 형식 만료시간 (YYYYMMDDHHMISS)
    
    /**
     * 토큰이 6시간 이내에 발급되었는지 확인 (재활용 가능)
     */
    public boolean isReusable() {
        return issuedAt != null && issuedAt.isAfter(LocalDateTime.now().minusHours(6));
    }
    
    /**
     * 토큰이 만료되었는지 확인
     */
    public boolean isExpired() {
        return expiresAt != null && expiresAt.isBefore(LocalDateTime.now());
    }
    
    /**
     * 토큰이 유효한지 확인 (만료되지 않음)
     */
    public boolean isValid() {
        return !isExpired();
    }
}