package com.quantum.user.presentation.web

import com.quantum.user.application.port.incoming.AuthUseCase
import com.quantum.user.application.port.incoming.LoginCommand
import com.quantum.user.application.port.incoming.UserInfo
import com.quantum.user.infrastructure.security.CustomUserDetails
import com.quantum.user.presentation.dto.LoginRequest
import com.quantum.user.presentation.dto.LoginResponse
import com.quantum.user.presentation.dto.UserResponse
import com.quantum.user.presentation.dto.ErrorResponse
import com.quantum.user.presentation.dto.SuccessResponse
import jakarta.validation.Valid
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.security.core.annotation.AuthenticationPrincipal
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/v1/auth")
class AuthController(
    private val authUseCase: AuthUseCase
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    @PostMapping("/login")
    fun login(@Valid @RequestBody request: LoginRequest): ResponseEntity<*> {
        logger.info("Login request for email: ${request.email}")
        
        val command = LoginCommand(
            email = request.email,
            password = request.password
        )
        
        val result = authUseCase.login(command)
        
        return if (result.success) {
            val response = LoginResponse(
                accessToken = result.accessToken!!,
                expiresIn = result.expiresIn!!,
                user = mapToUserResponse(result.user!!)
            )
            ResponseEntity.ok(response)
        } else {
            logger.warn("Login failed for email: ${request.email}, reason: ${result.errorMessage}")
            ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(
                ErrorResponse(
                    error = "AUTHENTICATION_FAILED",
                    message = result.errorMessage ?: "인증에 실패했습니다."
                )
            )
        }
    }
    
    @GetMapping("/me")
    fun getCurrentUser(@AuthenticationPrincipal userDetails: CustomUserDetails): ResponseEntity<UserResponse> {
        logger.debug("Getting current user info for userId: ${userDetails.getUser().id}")
        
        val userInfo = authUseCase.getUserInfo(userDetails.getUser().id)
        val response = mapToUserResponse(userInfo)
        
        return ResponseEntity.ok(response)
    }
    
    @PostMapping("/logout")
    fun logout(@AuthenticationPrincipal userDetails: CustomUserDetails): ResponseEntity<SuccessResponse> {
        logger.info("Logout request for userId: ${userDetails.getUser().id}")
        
        val result = authUseCase.logout(userDetails.getUser().id)
        val response = SuccessResponse(message = result.message)
        
        return ResponseEntity.ok(response)
    }
    
    private fun mapToUserResponse(userInfo: UserInfo): UserResponse {
        return UserResponse(
            id = userInfo.id,
            email = userInfo.email,
            name = userInfo.name,
            roles = userInfo.roles,
            lastLoginAt = userInfo.lastLoginAt
        )
    }
}