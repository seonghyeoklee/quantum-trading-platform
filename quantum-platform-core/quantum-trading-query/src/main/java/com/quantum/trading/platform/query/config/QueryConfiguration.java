package com.quantum.trading.platform.query.config;

import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * Trading Query 모듈 설정
 * 
 * CQRS Query Side JPA 설정 및 트랜잭션 관리
 */
@Configuration
@EntityScan(basePackages = "com.quantum.trading.platform.query.view")
@EnableJpaRepositories(basePackages = "com.quantum.trading.platform.query.repository")
@EnableTransactionManagement
public class QueryConfiguration {
    
    // JPA 및 Repository 설정은 어노테이션으로 자동 구성
    // 필요시 추가 Bean 설정을 여기에 추가
}