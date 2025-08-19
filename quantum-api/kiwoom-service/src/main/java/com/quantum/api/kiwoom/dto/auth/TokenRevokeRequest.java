package com.quantum.api.kiwoom.dto.auth;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 키움증권 OAuth 토큰 폐기 요청 DTO
 * JSON 스펙: {"appkey": "...", "secretkey": "...", "token": "..."}
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TokenRevokeRequest {
    
    @JsonProperty("appkey")
    private String appkey;          // 키움 앱키
    
    @JsonProperty("secretkey")
    private String secretkey;       // 키움 시크릿키
    
    @JsonProperty("token")
    private String token;           // 폐기할 접근토큰
}