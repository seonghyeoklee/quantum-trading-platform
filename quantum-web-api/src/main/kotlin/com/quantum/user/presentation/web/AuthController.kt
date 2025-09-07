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
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.Parameter
import io.swagger.v3.oas.annotations.media.Content
import io.swagger.v3.oas.annotations.media.Schema
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.security.SecurityRequirement
import io.swagger.v3.oas.annotations.tags.Tag
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

/**
 * 사용자 인증 컨트롤러
 * 
 * 로그인, 로그아웃, 사용자 정보 조회 등 인증 관련 API 제공
 */
@RestController
@RequestMapping("/api/v1/auth")
@Tag(name = "Authentication", description = "사용자 인증 관리 API")
class AuthController(
    private val authUseCase: AuthUseCase
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    @PostMapping("/login")
    @Operation(
        summary = "사용자 로그인",
        description = "이메일과 비밀번호로 로그인하여 JWT 액세스 토큰을 발급받습니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200", 
            description = "로그인 성공", 
            content = [Content(schema = Schema(implementation = LoginResponse::class))]
        ),
        ApiResponse(
            responseCode = "401", 
            description = "인증 실패", 
            content = [Content(schema = Schema(implementation = ErrorResponse::class))]
        ),
        ApiResponse(
            responseCode = "400", 
            description = "잘못된 요청", 
            content = [Content(schema = Schema(implementation = ErrorResponse::class))]
        )
    )
    fun login(
        @Parameter(description = "로그인 요청 정보", required = true)
        @Valid @RequestBody request: LoginRequest
    ): ResponseEntity<*> {
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
    @Operation(
        summary = "현재 사용자 정보 조회",
        description = "JWT 토큰을 통해 인증된 현재 사용자의 정보를 조회합니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200", 
            description = "사용자 정보 조회 성공", 
            content = [Content(schema = Schema(implementation = UserResponse::class))]
        ),
        ApiResponse(
            responseCode = "401", 
            description = "인증되지 않은 사용자", 
            content = [Content(schema = Schema(implementation = ErrorResponse::class))]
        )
    )
    @SecurityRequirement(name = "bearerAuth")
    fun getCurrentUser(
        @Parameter(hidden = true) @AuthenticationPrincipal userDetails: CustomUserDetails
    ): ResponseEntity<UserResponse> {
        logger.debug("Getting current user info for userId: ${userDetails.getUser().id}")
        
        val userInfo = authUseCase.getUserInfo(userDetails.getUser().id)
        val response = mapToUserResponse(userInfo)
        
        return ResponseEntity.ok(response)
    }
    
    @PostMapping("/logout")
    @Operation(
        summary = "사용자 로그아웃",
        description = "현재 인증된 사용자의 세션을 종료합니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200", 
            description = "로그아웃 성공", 
            content = [Content(schema = Schema(implementation = SuccessResponse::class))]
        ),
        ApiResponse(
            responseCode = "401", 
            description = "인증되지 않은 사용자", 
            content = [Content(schema = Schema(implementation = ErrorResponse::class))]
        )
    )
    @SecurityRequirement(name = "bearerAuth")
    fun logout(
        @Parameter(hidden = true) @AuthenticationPrincipal userDetails: CustomUserDetails
    ): ResponseEntity<SuccessResponse> {
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