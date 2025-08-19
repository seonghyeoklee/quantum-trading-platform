package com.quantum.api.kiwoom.dto.auth;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * OAuth 토큰 발급 응답 DTO
 * 키움증권 API 스펙 및 일반 OAuth 2.0 호환
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TokenResponse {
    // 일반 OAuth 2.0 필드
    private String accessToken;     // 접근 토큰
    private String tokenType;       // Bearer
    private Long expiresIn;         // 만료 시간 (초)
    private String refreshToken;    // 리프레시 토큰
    private String scope;           // 권한 범위
    
    // 키움증권 API 전용 필드
    private String expiresDt;       // 만료일시 (YYYYMMDDHHMISS)
    private String token;           // 키움 토큰 (accessToken과 동일)
}