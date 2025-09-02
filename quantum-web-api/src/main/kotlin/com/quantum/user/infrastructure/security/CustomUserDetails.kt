package com.quantum.user.infrastructure.security

import com.quantum.user.domain.User
import com.quantum.user.domain.UserStatus
import org.springframework.security.core.GrantedAuthority
import org.springframework.security.core.authority.SimpleGrantedAuthority
import org.springframework.security.core.userdetails.UserDetails

/**
 * Spring Security UserDetails 구현체
 */
class CustomUserDetails(
    private val user: User
) : UserDetails {
    
    override fun getAuthorities(): Collection<GrantedAuthority> {
        return user.roles.map { SimpleGrantedAuthority("ROLE_${it.name}") }
    }
    
    override fun getPassword(): String {
        return user.password
    }
    
    override fun getUsername(): String {
        return user.email
    }
    
    override fun isAccountNonExpired(): Boolean {
        return user.status != UserStatus.SUSPENDED
    }
    
    override fun isAccountNonLocked(): Boolean {
        return user.status != UserStatus.SUSPENDED
    }
    
    override fun isCredentialsNonExpired(): Boolean {
        return true
    }
    
    override fun isEnabled(): Boolean {
        return user.status == UserStatus.ACTIVE
    }
    
    /**
     * User 도메인 객체 반환
     */
    fun getUser(): User {
        return user
    }
}