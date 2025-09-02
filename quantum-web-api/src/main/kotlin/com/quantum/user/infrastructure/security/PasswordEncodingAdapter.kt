package com.quantum.user.infrastructure.security

import com.quantum.user.application.port.outgoing.PasswordEncodingPort
import org.springframework.security.crypto.password.PasswordEncoder
import org.springframework.stereotype.Component

/**
 * 비밀번호 인코딩 어댑터
 */
@Component
class PasswordEncodingAdapter(
    private val passwordEncoder: PasswordEncoder
) : PasswordEncodingPort {
    
    override fun encode(rawPassword: String): String {
        return passwordEncoder.encode(rawPassword)
    }
    
    override fun matches(rawPassword: String, encodedPassword: String): Boolean {
        return passwordEncoder.matches(rawPassword, encodedPassword)
    }
}