package com.quantum.trading.platform.query.config;

import org.hibernate.envers.AuditReader;
import org.hibernate.envers.AuditReaderFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.envers.repository.support.EnversRevisionRepositoryFactoryBean;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;

/**
 * Hibernate Envers 감사 기능 설정
 * 
 * 핵심 엔티티의 변경 이력을 자동으로 추적하여
 * 데이터 변경 감사 및 이력 조회 기능 제공
 */
@Configuration
@EnableJpaRepositories(
    basePackages = "com.quantum.trading.platform.query.repository",
    repositoryFactoryBeanClass = EnversRevisionRepositoryFactoryBean.class
)
public class EnversConfig {
    
    @PersistenceContext
    private EntityManager entityManager;
    
    /**
     * AuditReader Bean 등록
     * 감사 이력 조회를 위한 Envers AuditReader
     */
    @Bean
    public AuditReader auditReader() {
        return AuditReaderFactory.get(entityManager);
    }
}