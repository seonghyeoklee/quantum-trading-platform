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
    
    /**
     * 비밀번호 강도 검증
     */
    fun validatePasswordStrength(password: String): PasswordValidationResult {
        val errors = mutableListOf<String>()
        
        if (password.length < 6) {
            errors.add("비밀번호는 최소 6자 이상이어야 합니다.")
        }
        
        if (password.length > 100) {
            errors.add("비밀번호는 100자를 초과할 수 없습니다.")
        }
        
        if (!password.any { it.isDigit() }) {
            errors.add("비밀번호는 최소 1개의 숫자를 포함해야 합니다.")
        }
        
        if (!password.any { it.isLetter() }) {
            errors.add("비밀번호는 최소 1개의 문자를 포함해야 합니다.")
        }
        
        return PasswordValidationResult(
            isValid = errors.isEmpty(),
            errors = errors
        )
    }
    
    /**
     * 사용자 생성 전 유효성 검사
     */
    fun validateUserCreation(email: String, name: String, password: String): UserCreationValidationResult {
        val errors = mutableListOf<String>()
        
        // 이메일 검증
        if (!validateEmail(email)) {
            errors.add("올바르지 않은 이메일 형식입니다.")
        }
        
        // 이름 검증
        if (name.isBlank()) {
            errors.add("이름은 필수 항목입니다.")
        } else if (name.length > 50) {
            errors.add("이름은 50자를 초과할 수 없습니다.")
        }
        
        // 비밀번호 검증
        val passwordValidation = validatePasswordStrength(password)
        if (!passwordValidation.isValid) {
            errors.addAll(passwordValidation.errors)
        }
        
        return UserCreationValidationResult(
            isValid = errors.isEmpty(),
            errors = errors
        )
    }
    
    /**
     * 두 사용자가 동일한지 확인
     */
    fun isSameUser(user1: User, user2: User): Boolean {
        return user1.id == user2.id
    }
}

/**
 * 비밀번호 유효성 검사 결과
 */
data class PasswordValidationResult(
    val isValid: Boolean,
    val errors: List<String>
)

/**
 * 사용자 생성 유효성 검사 결과  
 */
data class UserCreationValidationResult(
    val isValid: Boolean,
    val errors: List<String>
)