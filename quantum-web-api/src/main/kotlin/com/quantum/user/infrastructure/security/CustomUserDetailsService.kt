package com.quantum.user.infrastructure.security

import com.quantum.user.application.port.outgoing.UserRepository
import org.springframework.security.core.userdetails.UserDetails
import org.springframework.security.core.userdetails.UserDetailsService
import org.springframework.security.core.userdetails.UsernameNotFoundException
import org.springframework.stereotype.Component

/**
 * Spring Security UserDetailsService 구현체
 * 인프라스트럭처 계층의 보안 어댑터
 */
@Component
class CustomUserDetailsService(
    private val userRepository: UserRepository
) : UserDetailsService {
    
    override fun loadUserByUsername(username: String): UserDetails {
        val user = userRepository.findByEmail(username)
            .orElseThrow { UsernameNotFoundException("User not found with email: $username") }
        
        return CustomUserDetails(user)
    }
}