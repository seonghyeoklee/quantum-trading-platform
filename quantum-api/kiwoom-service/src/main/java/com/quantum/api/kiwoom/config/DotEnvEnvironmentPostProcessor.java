package com.quantum.api.kiwoom.config;

import io.github.cdimascio.dotenv.Dotenv;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.env.EnvironmentPostProcessor;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.MapPropertySource;

import java.util.HashMap;
import java.util.Map;

/**
 * .env 파일을 Spring Boot 애플리케이션 시작 시 로드하는 EnvironmentPostProcessor
 * 
 * Spring Boot의 Environment가 초기화되는 단계에서 실행되어
 * .env 파일의 환경변수를 Spring Environment에 주입합니다.
 */
public class DotEnvEnvironmentPostProcessor implements EnvironmentPostProcessor {

    @Override
    public void postProcessEnvironment(ConfigurableEnvironment environment, SpringApplication application) {
        try {
            // .env 파일 로드
            Dotenv dotenv = Dotenv.configure()
                    .ignoreIfMissing()
                    .load();

            // 환경변수를 Map으로 변환
            Map<String, Object> dotEnvProperties = new HashMap<>();
            for (var entry : dotenv.entries()) {
                String key = entry.getKey();
                String value = entry.getValue();
                
                // 이미 설정된 환경변수가 없는 경우만 추가
                if (!environment.containsProperty(key)) {
                    dotEnvProperties.put(key, value);
                    
                    // 시스템 프로퍼티로도 설정 (System.getenv()에서 접근 가능하도록)
                    System.setProperty(key, value);
                    
                    // 시작 시 로그 출력 (민감한 정보 마스킹)
                    if (isSensitiveKey(key)) {
                        System.out.println("[DotEnv] " + key + "=*** (시스템 프로퍼티 설정됨)");
                    } else {
                        System.out.println("[DotEnv] " + key + "=" + value + " (시스템 프로퍼티 설정됨)");
                    }
                }
            }

            // Spring Environment에 PropertySource 추가
            if (!dotEnvProperties.isEmpty()) {
                environment.getPropertySources().addFirst(
                    new MapPropertySource("dotEnvPropertySource", dotEnvProperties)
                );
                System.out.println("[DotEnv] " + dotEnvProperties.size() + "개의 환경변수를 로드했습니다.");
            }

        } catch (Exception e) {
            System.err.println("[DotEnv] .env 파일 로드 실패: " + e.getMessage());
        }
    }

    /**
     * 민감한 키 확인
     */
    private boolean isSensitiveKey(String key) {
        String lowerKey = key.toLowerCase();
        return lowerKey.contains("secret") || 
               lowerKey.contains("password") || 
               lowerKey.contains("key") || 
               lowerKey.contains("token");
    }
}