package com.quantum.api;

import java.util.TimeZone;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableFeignClients(basePackages = {"com.quantum"})
@ComponentScan(
        basePackages = {
            "com.quantum.api", // API 모듈 자체
            "com.quantum.core", // 코어 모듈
            "com.quantum.batch", // 배치 모듈 (KisTokenService 등)
            "com.quantum.kis" // KIS adapter (설정은 KisApiAdapterConfig에서 처리)
        })
@EntityScan(basePackages = {"com.quantum.core"})
@EnableAsync(proxyTargetClass = true)
@EnableAspectJAutoProxy(proxyTargetClass = true)
public class QuantumTradingApiApplication {
    public static void main(final String[] args) {
        // Set default timezone to Asia/Seoul for the JVM
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"));
        SpringApplication.run(QuantumTradingApiApplication.class, args);
    }
}
