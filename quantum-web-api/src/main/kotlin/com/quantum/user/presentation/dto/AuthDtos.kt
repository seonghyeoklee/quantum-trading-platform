package com.quantum.user.presentation.dto

import jakarta.validation.constraints.Email
import jakarta.validation.constraints.NotBlank
import jakarta.validation.constraints.Size

data class LoginRequest(
    @field:NotBlank(message = "이메일은 필수 항목입니다.")
    @field:Email(message = "올바른 이메일 형식이 아닙니다.")
    val email: String,
    
    @field:NotBlank(message = "비밀번호는 필수 항목입니다.")
    @field:Size(min = 6, max = 100, message = "비밀번호는 6자 이상 100자 이하여야 합니다.")
    val password: String
)

data class LoginResponse(
    val accessToken: String,
    val expiresIn: Long,
    val user: UserResponse
)

data class UserResponse(
    val id: Long,
    val email: String,
    val name: String,
    val roles: Set<String>,
    val lastLoginAt: String?
)

data class ErrorResponse(
    val error: String,
    val message: String,
    val timestamp: String = java.time.LocalDateTime.now().toString()
)

data class SuccessResponse(
    val message: String,
    val timestamp: String = java.time.LocalDateTime.now().toString()
)