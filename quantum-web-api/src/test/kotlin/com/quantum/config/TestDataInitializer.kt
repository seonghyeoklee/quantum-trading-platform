package com.quantum.config

import com.quantum.user.domain.User
import com.quantum.user.domain.UserRole
import com.quantum.user.domain.UserStatus
import com.quantum.user.application.port.outgoing.UserRepository
import org.slf4j.LoggerFactory
import org.springframework.boot.CommandLineRunner
import org.springframework.context.annotation.Profile
import org.springframework.security.crypto.password.PasswordEncoder
import org.springframework.stereotype.Component

/**
 * 테스트용 데이터 초기화
 */
@Component
@Profile("test")
class TestDataInitializer(
    private val userRepository: UserRepository,
    private val passwordEncoder: PasswordEncoder
) : CommandLineRunner {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    override fun run(vararg args: String?) {
        logger.info("테스트 데이터 초기화 시작...")
        
        if (userRepository.findByEmail("admin@quantum.local").isEmpty) {
            val admin = User(
                email = "admin@quantum.local",
                name = "Quantum Admin",
                password = passwordEncoder.encode("admin123"),
                status = UserStatus.ACTIVE
            )
            admin.addRole(UserRole.ADMIN)
            admin.addRole(UserRole.TRADER)
            
            userRepository.save(admin)
            logger.info("기본 관리자 계정 생성 완료: admin@quantum.local")
        }
        
        logger.info("테스트 데이터 초기화 완료")
    }
}