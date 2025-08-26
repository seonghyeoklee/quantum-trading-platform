package com.quantum.web.exception;

import com.quantum.web.controller.KiwoomAccountController;
import com.quantum.web.service.KiwoomAccountManagementService;
import com.quantum.web.service.KiwoomTokenService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 글로벌 예외 처리 핸들러
 * 
 * 모든 REST API 예외를 일관된 형식으로 처리하고 응답
 * - 키움증권 계정 관리 예외
 * - 인증/인가 예외
 * - 유효성 검증 예외
 * - 시스템 예외
 */
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    /**
     * 키움증권 계정 관리 예외 처리
     */
    @ExceptionHandler(KiwoomAccountManagementService.KiwoomAccountManagementException.class)
    public ResponseEntity<ErrorResponse> handleKiwoomAccountManagementException(
            KiwoomAccountManagementService.KiwoomAccountManagementException ex,
            WebRequest request) {
        
        log.warn("Kiwoom account management error: {}", ex.getMessage(), ex);
        
        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .message(ex.getMessage())
                .errorCode("KIWOOM_ACCOUNT_ERROR")
                .timestamp(Instant.now())
                .path(getPath(request))
                .build();
        
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
    }

    /**
     * 키움증권 토큰 관리 예외 처리
     */
    @ExceptionHandler(KiwoomTokenService.TokenManagementException.class)
    public ResponseEntity<ErrorResponse> handleTokenManagementException(
            KiwoomTokenService.TokenManagementException ex,
            WebRequest request) {
        
        log.warn("Kiwoom token management error: {}", ex.getMessage(), ex);
        
        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .message(ex.getMessage())
                .errorCode("TOKEN_MANAGEMENT_ERROR")
                .timestamp(Instant.now())
                .path(getPath(request))
                .build();
        
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
    }

    /**
     * 인증 예외 처리
     */
    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ErrorResponse> handleAuthenticationException(
            AuthenticationException ex,
            WebRequest request) {
        
        log.warn("Authentication error: {}", ex.getMessage());
        
        String message = ex instanceof BadCredentialsException 
            ? "Invalid username or password" 
            : "Authentication failed";
        
        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .message(message)
                .errorCode("AUTHENTICATION_ERROR")
                .timestamp(Instant.now())
                .path(getPath(request))
                .build();
        
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(errorResponse);
    }

    /**
     * 접근 권한 예외 처리
     */
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleAccessDeniedException(
            AccessDeniedException ex,
            WebRequest request) {
        
        log.warn("Access denied: {}", ex.getMessage());
        
        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .message("Access denied. Insufficient privileges.")
                .errorCode("ACCESS_DENIED")
                .timestamp(Instant.now())
                .path(getPath(request))
                .build();
        
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(errorResponse);
    }

    /**
     * 요청 본문 유효성 검증 실패 처리
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleMethodArgumentNotValidException(
            MethodArgumentNotValidException ex,
            WebRequest request) {
        
        log.debug("Validation error: {}", ex.getMessage());
        
        BindingResult bindingResult = ex.getBindingResult();
        Map<String, String> fieldErrors = new HashMap<>();
        
        for (FieldError fieldError : bindingResult.getFieldErrors()) {
            fieldErrors.put(fieldError.getField(), fieldError.getDefaultMessage());
        }
        
        String message = "Validation failed for " + fieldErrors.size() + " field(s)";
        
        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .message(message)
                .errorCode("VALIDATION_ERROR")
                .data(fieldErrors)
                .timestamp(Instant.now())
                .path(getPath(request))
                .build();
        
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
    }

    /**
     * 경로 매개변수 유효성 검증 실패 처리
     */
    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ErrorResponse> handleConstraintViolationException(
            ConstraintViolationException ex,
            WebRequest request) {
        
        log.debug("Constraint violation: {}", ex.getMessage());
        
        String violations = ex.getConstraintViolations()
                .stream()
                .map(ConstraintViolation::getMessage)
                .collect(Collectors.joining(", "));
        
        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .message("Validation failed: " + violations)
                .errorCode("CONSTRAINT_VIOLATION")
                .timestamp(Instant.now())
                .path(getPath(request))
                .build();
        
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
    }

    /**
     * 잘못된 인수 예외 처리
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handleIllegalArgumentException(
            IllegalArgumentException ex,
            WebRequest request) {
        
        log.debug("Illegal argument: {}", ex.getMessage());
        
        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .message("Invalid request: " + ex.getMessage())
                .errorCode("INVALID_ARGUMENT")
                .timestamp(Instant.now())
                .path(getPath(request))
                .build();
        
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
    }

    /**
     * 일반적인 런타임 예외 처리
     */
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<ErrorResponse> handleRuntimeException(
            RuntimeException ex,
            WebRequest request) {
        
        log.error("Runtime error: {}", ex.getMessage(), ex);
        
        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .message("An unexpected error occurred. Please try again later.")
                .errorCode("RUNTIME_ERROR")
                .timestamp(Instant.now())
                .path(getPath(request))
                .build();
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
    }

    /**
     * 모든 예외의 최종 처리
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(
            Exception ex,
            WebRequest request) {
        
        log.error("Unexpected error: {}", ex.getMessage(), ex);
        
        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .message("An internal server error occurred. Please contact support.")
                .errorCode("INTERNAL_SERVER_ERROR")
                .timestamp(Instant.now())
                .path(getPath(request))
                .build();
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
    }

    /**
     * 요청 경로 추출
     */
    private String getPath(WebRequest request) {
        String path = request.getDescription(false);
        return path.startsWith("uri=") ? path.substring(4) : path;
    }

    /**
     * 에러 응답 DTO
     */
    @lombok.Data
    @lombok.Builder
    public static class ErrorResponse {
        private boolean success;
        private String message;
        private String errorCode;
        private Object data;
        private Instant timestamp;
        private String path;
    }
}