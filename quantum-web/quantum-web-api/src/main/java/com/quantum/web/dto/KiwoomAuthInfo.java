package com.quantum.web.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 키움증권 인증 정보 DTO
 * 
 * 모드별 인증 정보 (토큰, API 키, 시크릿)를 담는 데이터 클래스
 * Python Adapter로 전달하여 환경변수 의존성 제거
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class KiwoomAuthInfo {
    
    /**
     * 액세스 토큰 (Bearer 토큰)
     */
    private String accessToken;
    
    /**
     * API 키 (앱키)
     */
    private String apiKey;
    
    /**
     * API 시크릿 (앱시크릿)
     */
    private String apiSecret;
    
    /**
     * 실전모드 여부
     */
    private boolean realMode;
    
    /**
     * 모드 설명 반환
     */
    public String getModeDescription() {
        return realMode ? "실전투자" : "모의투자";
    }
    
    /**
     * 키움 API 베이스 URL 반환
     */
    public String getBaseUrl() {
        return realMode ? 
                "https://api.kiwoom.com" : 
                "https://mockapi.kiwoom.com";
    }
    
    /**
     * WebSocket URL 반환
     */
    public String getWebSocketUrl() {
        return realMode ?
                "wss://api.kiwoom.com:10000/api/dostk/websocket" :
                "wss://mockapi.kiwoom.com:10000/api/dostk/websocket";
    }
    
    /**
     * 마스킹된 API 키 반환 (로깅용)
     */
    public String getMaskedApiKey() {
        if (apiKey == null || apiKey.length() < 8) {
            return "****";
        }
        return apiKey.substring(0, 4) + "****" + apiKey.substring(apiKey.length() - 4);
    }
    
    /**
     * 인증 정보 유효성 검증
     */
    public boolean isValid() {
        return accessToken != null && !accessToken.trim().isEmpty() &&
               apiKey != null && !apiKey.trim().isEmpty() &&
               apiSecret != null && !apiSecret.trim().isEmpty();
    }
}