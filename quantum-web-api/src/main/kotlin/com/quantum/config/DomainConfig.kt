package com.quantum.config

import com.quantum.user.domain.UserDomainService
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

/**
 * 도메인 서비스들의 Bean 등록을 위한 Configuration
 * 
 * 도메인 계층은 프레임워크에 독립적이므로 
 * 도메인 서비스들은 수동으로 Bean 등록
 */
@Configuration
class DomainConfig {
    
    /**
     * User 도메인 서비스 Bean 등록
     */
    @Bean
    fun userDomainService(): UserDomainService {
        return UserDomainService()
    }
}