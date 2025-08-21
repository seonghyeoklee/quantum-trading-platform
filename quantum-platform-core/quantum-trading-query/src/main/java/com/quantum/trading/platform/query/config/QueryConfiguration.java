package com.quantum.trading.platform.query.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * Trading Query 모듈 설정
 * 
 * CQRS Query Side 트랜잭션 관리
 * 
 * 참고: @EntityScan과 @EnableJpaRepositories는 
 * 메인 애플리케이션(QuantumWebApiApplication)에서 설정됨
 */
@Configuration
@EnableTransactionManagement
public class QueryConfiguration {
    
    // JPA 및 Repository 설정은 메인 애플리케이션에서 구성
    // 필요시 추가 Bean 설정을 여기에 추가
}