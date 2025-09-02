package com.quantum.user.infrastructure.persistence

import com.quantum.user.application.port.outgoing.UserRepository
import com.quantum.user.domain.User
import org.springframework.stereotype.Repository
import java.util.*

/**
 * UserRepository 포트의 JPA 구현체 (헥사고날 아키텍처의 어댑터)
 */
@Repository
class UserRepositoryImpl(
    private val userJpaRepository: UserJpaRepository
) : UserRepository {
    
    override fun save(user: User): User {
        return userJpaRepository.save(user)
    }
    
    override fun findById(id: Long): Optional<User> {
        return userJpaRepository.findById(id)
    }
    
    override fun findByEmail(email: String): Optional<User> {
        return userJpaRepository.findByEmail(email)
    }
    
    override fun existsByEmail(email: String): Boolean {
        return userJpaRepository.existsByEmail(email)
    }
    
    override fun findAll(): List<User> {
        return userJpaRepository.findAll()
    }
    
    override fun delete(user: User) {
        userJpaRepository.delete(user)
    }
    
    override fun deleteById(id: Long) {
        userJpaRepository.deleteById(id)
    }
}