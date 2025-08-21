package com.quantum.api.kiwoom.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.ConfigurableEnvironment;

import jakarta.annotation.PostConstruct;

/**
 * DotEnv 설정 클래스
 *
 * .env 파일은 DotEnvEnvironmentPostProcessor에서 로드되며,
 * 이 클래스는 로드된 환경변수를 검증하는 역할을 합니다.
 */
@Configuration
@Slf4j
public class DotEnvConfig {

    private final ConfigurableEnvironment environment;

    public DotEnvConfig(ConfigurableEnvironment environment) {
        this.environment = environment;
    }

    /**
     * 키움 API 설정 검증
     */
//    @PostConstruct
//    public void validateKiwoomConfig() {
//        String mode = environment.getProperty("KIWOOM_MODE", "mock");
//
//        String appKey;
//        String appSecret;
//
//        if ("production".equalsIgnoreCase(mode) || "prod".equalsIgnoreCase(mode)) {
//            appKey = environment.getProperty("KIWOOM_PROD_APP_KEY");
//            appSecret = environment.getProperty("KIWOOM_PROD_APP_SECRET");
//            log.info("키움 API 모드: 실전투자 (Production)");
//        } else {
//            appKey = environment.getProperty("KIWOOM_MOCK_APP_KEY");
//            appSecret = environment.getProperty("KIWOOM_MOCK_APP_SECRET");
//            log.info("키움 API 모드: 모의투자 (Mock)");
//        }
//
//        if (appKey == null || appKey.trim().isEmpty()) {
//            log.error("키움 API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.");
//        } else {
//            log.info("키움 API 키 확인 완료: {}***", appKey.substring(0, Math.min(8, appKey.length())));
//        }
//
//        if (appSecret == null || appSecret.trim().isEmpty()) {
//            log.error("키움 API 시크릿이 설정되지 않았습니다. .env 파일을 확인해주세요.");
//        } else {
//            log.info("키움 API 시크릿 확인 완료: {}***", appSecret.substring(0, Math.min(8, appSecret.length())));
//        }
//    }
}
