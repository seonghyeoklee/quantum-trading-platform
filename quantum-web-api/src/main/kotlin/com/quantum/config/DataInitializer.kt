package com.quantum.config

import com.quantum.user.application.port.outgoing.PasswordEncodingPort
import com.quantum.user.application.port.outgoing.UserRepository
import com.quantum.user.domain.User
import com.quantum.user.domain.UserRole
import jakarta.annotation.PostConstruct
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Component

/**
 * 초기 데이터 생성
 */
@Component
class DataInitializer(
    private val userRepository: UserRepository,
    private val passwordEncodingPort: PasswordEncodingPort
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    @PostConstruct
    fun initializeData() {
        createAdminUser()
    }
    
    private fun createAdminUser() {
        val adminEmail = "admin@quantum.local"
        
        // 이미 admin 사용자가 존재하는지 확인
        if (userRepository.existsByEmail(adminEmail)) {
            logger.info("Admin user already exists")
            return
        }
        
        // admin 사용자 생성
        val adminUser = User(
            email = adminEmail,
            name = "Quantum Admin",
            password = passwordEncodingPort.encode("admin123")
        )
        
        // admin 권한 추가
        adminUser.addRole(UserRole.ADMIN)
        adminUser.addRole(UserRole.TRADER)
        
        userRepository.save(adminUser)
        
        logger.info("Admin user created successfully: $adminEmail")
        logger.info("Default password: admin123")
        logger.warn("Please change the default password in production!")
    }
}