package com.quantum.user.domain

/**
 * User 도메인 서비스
 * 복잡한 도메인 로직이나 여러 애그리게이트 간의 비즈니스 규칙을 처리
 * 
 * 도메인 계층은 프레임워크에 독립적이므로 Spring 애노테이션을 사용하지 않음
 */
class UserDomainService {
    
    /**
     * 이메일 유효성 검증
     */
    fun validateEmail(email: String): Boolean {
        val emailRegex = "^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"
        return email.matches(emailRegex.toRegex())
    }
}