package com.quantum.api.kiwoom;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
import org.springframework.context.annotation.ComponentScan;

/**
 * 키움증권 API 서비스 메인 애플리케이션
 * 
 * - 독립적인 마이크로서비스로 실행
 * - 루트 도메인 접속 시 Swagger UI로 리다이렉트
 * - 키움증권 API 연동 기능 제공
 */
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})
@ComponentScan(basePackages = {
    "com.quantum.api.kiwoom",
    "com.quantum.trading.platform.broker.kiwoom"
})
@Slf4j
public class KiwoomApiApplication {
    
    public static void main(String[] args) {
        log.info("Starting Kiwoom API Service...");
        SpringApplication.run(KiwoomApiApplication.class, args);
        log.info("Kiwoom API Service started successfully!");
    }
}