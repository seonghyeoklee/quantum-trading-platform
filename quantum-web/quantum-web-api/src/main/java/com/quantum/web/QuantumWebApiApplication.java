package com.quantum.web;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * Quantum Trading Platform Web API Application
 *
 * React/Next.js 프론트엔드를 위한 REST API 및 WebSocket 서버
 * 차트 데이터, 실시간 시세, 거래 API 제공
 */
@SpringBootApplication
@EnableAsync
@ComponentScan(basePackages = {
    "com.quantum.web",                           // Web API 컴포넌트
    "com.quantum.trading.platform.query"        // Query Side 컴포넌트
})
@EntityScan(basePackages = {
    "com.quantum.trading.platform.query.view"   // JPA Entities (Read Models)
})
@EnableJpaRepositories(basePackages = {
    "com.quantum.trading.platform.query.repository" // Query Side Repositories
})
public class QuantumWebApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(QuantumWebApiApplication.class, args);
    }
}
