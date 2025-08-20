package com.quantum.api.kiwoom.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 키움증권 API 설정 프로퍼티
 * 실전투자와 모의투자 키를 분리하여 관리
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "kiwoom.api")
public class KiwoomProperties {
    
    /**
     * 현재 모드 (production 또는 mock)
     */
    private String mode = "mock";
    
    /**
     * 실전투자 API URL
     */
    private String baseUrl = "https://api.kiwoom.com";
    
    /**
     * 모의투자 API URL
     */
    private String mockUrl = "https://mockapi.kiwoom.com";
    
    /**
     * 계좌번호
     */
    private String accountNumber;
    
    /**
     * 타임아웃 (밀리초)
     */
    private int timeout = 30000;
    
    /**
     * 실전투자 인증 정보
     */
    private Credentials prod = new Credentials();
    
    /**
     * 모의투자 인증 정보
     */
    private Credentials mock = new Credentials();
    
    /**
     * 인증 정보 클래스
     */
    @Data
    public static class Credentials {
        private String appKey;
        private String appSecret;
    }
    
    /**
     * 현재 모드에 따른 API URL 반환
     */
    public String getCurrentBaseUrl() {
        return isProductionMode() ? baseUrl : mockUrl;
    }
    
    /**
     * 현재 모드에 따른 앱키 반환
     */
    public String getCurrentAppKey() {
        return isProductionMode() ? prod.getAppKey() : mock.getAppKey();
    }
    
    /**
     * 현재 모드에 따른 시크릿키 반환
     */
    public String getCurrentAppSecret() {
        return isProductionMode() ? prod.getAppSecret() : mock.getAppSecret();
    }
    
    /**
     * 실전투자 모드 여부 확인
     */
    public boolean isProductionMode() {
        return "production".equalsIgnoreCase(mode) || "prod".equalsIgnoreCase(mode);
    }
    
    /**
     * 모의투자 모드 여부 확인
     */
    public boolean isMockMode() {
        return !isProductionMode();
    }
    
    /**
     * 현재 모드 문자열 반환
     */
    public String getModeDescription() {
        return isProductionMode() ? "실전투자" : "모의투자";
    }
}