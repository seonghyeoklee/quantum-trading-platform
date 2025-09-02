package com.quantum.user.infrastructure.persistence

import com.quantum.user.domain.User
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.stereotype.Repository
import java.util.*

/**
 * Spring Data JPA Repository 인터페이스
 */
@Repository
interface UserJpaRepository : JpaRepository<User, Long> {
    
    /**
     * 이메일로 사용자 조회
     */
    fun findByEmail(email: String): Optional<User>
    
    /**
     * 이메일 존재 여부 확인
     */
    fun existsByEmail(email: String): Boolean
    
    /**
     * 활성 사용자만 조회
     */
    @Query("SELECT u FROM User u WHERE u.status = 'ACTIVE'")
    fun findAllActiveUsers(): List<User>
}