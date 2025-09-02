package com.quantum.config

import com.quantum.user.presentation.dto.ErrorResponse
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.security.authentication.BadCredentialsException
import org.springframework.security.core.userdetails.UsernameNotFoundException
import org.springframework.validation.FieldError
import org.springframework.web.bind.MethodArgumentNotValidException
import org.springframework.web.bind.MissingServletRequestParameterException
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.RestControllerAdvice

@RestControllerAdvice
class GlobalExceptionHandler {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    @ExceptionHandler(MethodArgumentNotValidException::class)
    fun handleValidationExceptions(ex: MethodArgumentNotValidException): ResponseEntity<ErrorResponse> {
        val errors = ex.bindingResult.allErrors.joinToString(", ") { error ->
            when (error) {
                is FieldError -> "${error.field}: ${error.defaultMessage}"
                else -> error.defaultMessage ?: "Unknown validation error"
            }
        }

        logger.warn("Validation error: $errors")
        
        return ResponseEntity.badRequest().body(
            ErrorResponse(
                error = "VALIDATION_ERROR",
                message = errors
            )
        )
    }
    
    @ExceptionHandler(BadCredentialsException::class)
    fun handleBadCredentialsException(ex: BadCredentialsException): ResponseEntity<ErrorResponse> {
        logger.warn("Authentication failed: ${ex.message}")
        
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(
            ErrorResponse(
                error = "BAD_CREDENTIALS",
                message = "이메일 또는 비밀번호가 올바르지 않습니다."
            )
        )
    }
    
    @ExceptionHandler(UsernameNotFoundException::class)
    fun handleUsernameNotFoundException(ex: UsernameNotFoundException): ResponseEntity<ErrorResponse> {
        logger.warn("User not found: ${ex.message}")
        
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(
            ErrorResponse(
                error = "USER_NOT_FOUND",
                message = "사용자를 찾을 수 없습니다."
            )
        )
    }
    
    @ExceptionHandler(IllegalArgumentException::class)
    fun handleIllegalArgumentException(ex: IllegalArgumentException): ResponseEntity<ErrorResponse> {
        logger.warn("Illegal argument: ${ex.message}")
        
        return ResponseEntity.badRequest().body(
            ErrorResponse(
                error = "ILLEGAL_ARGUMENT",
                message = ex.message ?: "잘못된 요청입니다."
            )
        )
    }
    
    @ExceptionHandler(IllegalStateException::class)
    fun handleIllegalStateException(ex: IllegalStateException): ResponseEntity<ErrorResponse> {
        logger.warn("Illegal state: ${ex.message}")
        
        return ResponseEntity.status(HttpStatus.CONFLICT).body(
            ErrorResponse(
                error = "ILLEGAL_STATE",
                message = ex.message ?: "요청을 처리할 수 없는 상태입니다."
            )
        )
    }
    
    @ExceptionHandler(MissingServletRequestParameterException::class)
    fun handleMissingRequestParameter(ex: MissingServletRequestParameterException): ResponseEntity<ErrorResponse> {
        logger.warn("Missing request parameter: ${ex.parameterName}")
        
        val message = when (ex.parameterName) {
            "environment" -> "필수 파라미터 'environment'가 누락되었습니다. LIVE 또는 SANDBOX 중 선택해주세요."
            else -> "필수 파라미터 '${ex.parameterName}'가 누락되었습니다."
        }
        
        return ResponseEntity.badRequest().body(
            ErrorResponse(
                error = "MISSING_PARAMETER",
                message = message
            )
        )
    }
    
    @ExceptionHandler(MethodArgumentTypeMismatchException::class)
    fun handleTypeMismatch(ex: MethodArgumentTypeMismatchException): ResponseEntity<ErrorResponse> {
        logger.warn("Type mismatch for parameter: ${ex.name}")
        
        val message = when (ex.name) {
            "environment" -> "environment 파라미터는 LIVE 또는 SANDBOX 값만 허용됩니다."
            else -> "파라미터 '${ex.name}'의 값이 올바르지 않습니다."
        }
        
        return ResponseEntity.badRequest().body(
            ErrorResponse(
                error = "INVALID_PARAMETER",
                message = message
            )
        )
    }
    
    @ExceptionHandler(Exception::class)
    fun handleGenericException(ex: Exception): ResponseEntity<ErrorResponse> {
        logger.error("Unexpected error occurred", ex)
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(
            ErrorResponse(
                error = "INTERNAL_SERVER_ERROR",
                message = "서버 내부 오류가 발생했습니다."
            )
        )
    }
}