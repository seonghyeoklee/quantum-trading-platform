package com.quantum.config

import org.springframework.context.annotation.Configuration
import org.springframework.data.jpa.repository.config.EnableJpaAuditing
import org.springframework.data.jpa.repository.config.EnableJpaRepositories

/**
 * JPA 설정
 */
@Configuration
@EnableJpaAuditing
@EnableJpaRepositories(basePackages = [
    "com.quantum.*.infrastructure.persistence", 
    "com.quantum.*.infrastructure.repository"
])
class JpaConfig