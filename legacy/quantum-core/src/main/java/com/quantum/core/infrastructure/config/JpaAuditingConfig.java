package com.quantum.core.infrastructure.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

/**
 * JPA 설정
 *
 * <p>엔티티의 생성일시, 수정일시 등을 자동으로 관리하고 JPA Repository를 활성화합니다.
 */
@Configuration
@EnableJpaAuditing
@EnableJpaRepositories(basePackages = "com.quantum.core")
public class JpaAuditingConfig {}
