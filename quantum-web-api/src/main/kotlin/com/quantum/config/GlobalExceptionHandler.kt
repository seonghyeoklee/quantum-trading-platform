package com.quantum.config

import com.quantum.common.dto.ErrorCodes
import com.quantum.common.dto.StandardErrorResponse
import com.quantum.common.dto.UserMessages
import com.quantum.stock.application.service.StockDataException
import com.quantum.user.presentation.dto.ErrorResponse
import jakarta.servlet.http.HttpServletRequest
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
    
    // 주식 데이터 서비스 예외 처리 (표준화된 응답)
    @ExceptionHandler(StockDataException::class)
    fun handleStockDataException(
        ex: StockDataException, 
        request: HttpServletRequest
    ): ResponseEntity<StandardErrorResponse> {
        logger.error("Stock data service error: ${ex.message}", ex)
        
        val errorResponse = StandardErrorResponse.dataNotFound(
            message = ex.message ?: UserMessages.STOCK_NOT_FOUND,
            path = request.requestURI
        )
        
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse)
    }
    
    // KIS API 관련 오류 처리 (표준화된 응답)
    @ExceptionHandler(RuntimeException::class)
    fun handleKisApiException(
        ex: RuntimeException,
        request: HttpServletRequest
    ): ResponseEntity<StandardErrorResponse> {
        val message = ex.message ?: ""
        
        // KIS API 관련 오류 패턴 감지
        when {
            message.contains("KIS", ignoreCase = true) || 
            message.contains("token", ignoreCase = true) ||
            message.contains("API", ignoreCase = true) -> {
                logger.error("KIS API error occurred: ${ex.message}", ex)
                
                val errorResponse = StandardErrorResponse.kisApiError(
                    UserMessages.KIS_API_CONNECTION_FAILED
                ).copy(path = request.requestURI)
                
                return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(errorResponse)
            }
            message.contains("데이터", ignoreCase = true) ||
            message.contains("data", ignoreCase = true) -> {
                logger.error("Data processing error: ${ex.message}", ex)
                
                val errorResponse = StandardErrorResponse(
                    error = ErrorCodes.DATA_INTEGRITY_ERROR,
                    message = UserMessages.CHART_DATA_NOT_AVAILABLE,
                    details = "데이터 처리 중 오류가 발생했습니다.",
                    path = request.requestURI
                )
                
                return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).body(errorResponse)
            }
            else -> {
                logger.error("Runtime error occurred: ${ex.message}", ex)
                
                val errorResponse = StandardErrorResponse.internalServerError(
                    UserMessages.SERVER_ERROR
                ).copy(path = request.requestURI)
                
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse)
            }
        }
    }
    
    // 일반적인 오류는 더 구체적인 정보 없이 처리 (표준화된 응답)
    @ExceptionHandler(Exception::class)
    fun handleGenericException(
        ex: Exception,
        request: HttpServletRequest
    ): ResponseEntity<StandardErrorResponse> {
        logger.error("Unexpected error occurred", ex)
        
        // 절대 더미 데이터를 생성하거나 성공으로 위장하지 않음
        val errorResponse = StandardErrorResponse.internalServerError(
            UserMessages.SERVER_ERROR
        ).copy(
            details = "예기치 않은 오류가 발생했습니다.",
            path = request.requestURI
        )
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse)
    }
}