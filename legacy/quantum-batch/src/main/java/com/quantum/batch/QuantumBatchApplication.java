package com.quantum.batch;

import java.util.TimeZone;
import org.springframework.batch.core.configuration.annotation.EnableBatchProcessing;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableBatchProcessing
@EnableScheduling
@EnableFeignClients(basePackages = {"com.quantum"})
@ComponentScan(basePackages = {
    "com.quantum.batch",    // 배치 모듈 자체
    "com.quantum.core",     // 코어 모듈
    "com.quantum.kis"       // KIS adapter (설정은 KisAdapterConfig에서 처리)
})
@EntityScan(basePackages = {"com.quantum.core"})
@EnableAsync(proxyTargetClass = true)
@EnableAspectJAutoProxy(proxyTargetClass = true)
public class QuantumBatchApplication {

    public static void main(final String[] args) {
        // Set default timezone to Asia/Seoul for the JVM
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"));
        SpringApplication.run(QuantumBatchApplication.class, args);
    }
}
