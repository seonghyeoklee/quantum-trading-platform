package com.quantum.api.kiwoom.dto.auth;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 키움증권 OAuth 토큰 발급 요청 DTO
 * JSON 스펙: {"grant_type": "client_credentials", "appkey": "...", "secretkey": "..."}
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TokenRequest {
    @JsonProperty("grant_type")
    private String grantType;       // "client_credentials" 고정
    
    @JsonProperty("appkey")
    private String appkey;          // 키움 앱키
    
    @JsonProperty("secretkey")
    private String secretkey;       // 키움 시크릿키
    
    // 기존 필드들 (호환성을 위해 유지)
    private String appKey;          // 앱 키 (호환용)
    private String appSecret;       // 앱 시크릿 (호환용)
    private String code;            // 인가 코드
    private String refreshToken;    // 리프레시 토큰
}