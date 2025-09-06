package com.quantum.user.domain

import org.springframework.stereotype.Component

/**
 * User 도메인 서비스
 * 복잡한 도메인 로직이나 여러 애그리게이트 간의 비즈니스 규칙을 처리
 */
@Component
class UserDomainService {
    
    /**
     * 이메일 유효성 검증
     */
    fun validateEmail(email: String): Boolean {
        val emailRegex = "^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"
        return email.matches(emailRegex.toRegex())
    }
}