package com.quantum.user.application.port.outgoing

import com.quantum.user.domain.User
import java.util.*

/**
 * User Repository 포트 (헥사고날 아키텍처의 아웃고잉 포트)
 * 도메인이 인프라스트럭처에 의존하지 않도록 하는 인터페이스
 */
interface UserRepository {
    
    /**
     * 사용자 저장
     */
    fun save(user: User): User
    
    /**
     * ID로 사용자 조회
     */
    fun findById(id: Long): Optional<User>
    
    /**
     * 이메일로 사용자 조회
     */
    fun findByEmail(email: String): Optional<User>
    
    /**
     * 사용자 존재 여부 확인 (이메일)
     */
    fun existsByEmail(email: String): Boolean
    
    /**
     * 모든 사용자 조회
     */
    fun findAll(): List<User>
    
    /**
     * 사용자 삭제
     */
    fun delete(user: User)
    
    /**
     * ID로 사용자 삭제
     */
    fun deleteById(id: Long)
}