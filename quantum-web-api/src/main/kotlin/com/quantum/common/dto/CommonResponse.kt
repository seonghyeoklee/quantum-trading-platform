package com.quantum.common.dto

import java.time.LocalDateTime

/**
 * 표준화된 에러 응답 DTO
 * 
 * 모든 API에서 일관된 에러 응답 형식을 보장
 * 가짜 데이터 생성을 방지하고 실제 오류 정보만 포함
 */
data class StandardErrorResponse(
    val error: String,              // 에러 코드 (예: "VALIDATION_ERROR", "DATA_NOT_FOUND")
    val message: String,            // 사용자 친화적 메시지
    val details: String? = null,    // 상세 오류 정보 (선택적)
    val path: String? = null,       // 요청 경로 (선택적)
    val timestamp: String = LocalDateTime.now().toString(),
    val data: Any? = null           // 추가 데이터 (선택적, 절대 가짜 데이터 포함 안함)
) {
    companion object {
        /**
         * 데이터 조회 실패 응답
         */
        fun dataNotFound(message: String, path: String? = null): StandardErrorResponse {
            return StandardErrorResponse(
                error = "DATA_NOT_FOUND",
                message = message,
                path = path
            )
        }
        
        /**
         * 유효성 검증 실패 응답
         */
        fun validationFailed(message: String, details: String? = null): StandardErrorResponse {
            return StandardErrorResponse(
                error = "VALIDATION_ERROR",
                message = message,
                details = details
            )
        }
        
        /**
         * 외부 API 연결 실패 응답
         */
        fun externalApiError(message: String): StandardErrorResponse {
            return StandardErrorResponse(
                error = "EXTERNAL_API_ERROR",
                message = message
            )
        }
        
        /**
         * KIS API 특화 에러 응답
         */
        fun kisApiError(message: String): StandardErrorResponse {
            return StandardErrorResponse(
                error = "KIS_API_ERROR",
                message = message
            )
        }
        
        /**
         * 데이터베이스 오류 응답
         */
        fun databaseError(message: String): StandardErrorResponse {
            return StandardErrorResponse(
                error = "DATABASE_ERROR",
                message = message
            )
        }
        
        /**
         * 서버 내부 오류 응답
         */
        fun internalServerError(message: String = "서버 내부 오류가 발생했습니다."): StandardErrorResponse {
            return StandardErrorResponse(
                error = "INTERNAL_SERVER_ERROR",
                message = message
            )
        }
        
        /**
         * 인증 실패 응답
         */
        fun authenticationFailed(message: String = "인증에 실패했습니다."): StandardErrorResponse {
            return StandardErrorResponse(
                error = "AUTHENTICATION_FAILED",
                message = message
            )
        }
        
        /**
         * 권한 부족 응답
         */
        fun accessDenied(message: String = "접근 권한이 없습니다."): StandardErrorResponse {
            return StandardErrorResponse(
                error = "ACCESS_DENIED",
                message = message
            )
        }
    }
}

/**
 * 표준화된 성공 응답 DTO
 */
data class StandardSuccessResponse<T>(
    val success: Boolean = true,
    val message: String,
    val data: T? = null,
    val timestamp: String = LocalDateTime.now().toString()
) {
    companion object {
        /**
         * 데이터와 함께 성공 응답
         */
        fun <T> withData(data: T, message: String = "처리되었습니다."): StandardSuccessResponse<T> {
            return StandardSuccessResponse(
                message = message,
                data = data
            )
        }
        
        /**
         * 메시지만 포함하는 성공 응답
         */
        fun messageOnly(message: String): StandardSuccessResponse<Nothing> {
            return StandardSuccessResponse(
                message = message,
                data = null
            )
        }
    }
}

/**
 * API 에러 코드 상수
 * 
 * 에러 코드를 중앙에서 관리하여 일관성 보장
 */
object ErrorCodes {
    // 일반적인 에러
    const val VALIDATION_ERROR = "VALIDATION_ERROR"
    const val DATA_NOT_FOUND = "DATA_NOT_FOUND"
    const val INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    const val BAD_REQUEST = "BAD_REQUEST"
    
    // 인증/인가 에러
    const val AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    const val ACCESS_DENIED = "ACCESS_DENIED"
    const val TOKEN_EXPIRED = "TOKEN_EXPIRED"
    const val INVALID_TOKEN = "INVALID_TOKEN"
    
    // 외부 API 에러
    const val EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    const val KIS_API_ERROR = "KIS_API_ERROR"
    const val KIS_TOKEN_ERROR = "KIS_TOKEN_ERROR"
    const val API_RATE_LIMIT = "API_RATE_LIMIT"
    
    // 데이터베이스 에러
    const val DATABASE_ERROR = "DATABASE_ERROR"
    const val DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"
    const val TRANSACTION_FAILED = "TRANSACTION_FAILED"
    
    // 주식 관련 에러
    const val STOCK_NOT_FOUND = "STOCK_NOT_FOUND"
    const val INVALID_STOCK_CODE = "INVALID_STOCK_CODE"
    const val CHART_DATA_UNAVAILABLE = "CHART_DATA_UNAVAILABLE"
    const val PRICE_DATA_UNAVAILABLE = "PRICE_DATA_UNAVAILABLE"
}

/**
 * 사용자 친화적 메시지 상수
 */
object UserMessages {
    // 데이터 관련
    const val STOCK_NOT_FOUND = "요청하신 종목 정보를 찾을 수 없습니다."
    const val CHART_DATA_NOT_AVAILABLE = "차트 데이터를 불러올 수 없습니다."
    const val PRICE_DATA_NOT_AVAILABLE = "현재가 정보를 불러올 수 없습니다."
    
    // 외부 API 관련
    const val KIS_API_CONNECTION_FAILED = "KIS API 연결에 실패했습니다. 잠시 후 다시 시도해주세요."
    const val EXTERNAL_SERVICE_UNAVAILABLE = "외부 서비스에 일시적인 문제가 발생했습니다."
    
    // 일반적인 에러
    const val INVALID_REQUEST = "잘못된 요청입니다. 입력 정보를 확인해주세요."
    const val SERVER_ERROR = "서버 내부 오류가 발생했습니다. 관리자에게 문의하세요."
    const val RATE_LIMIT_EXCEEDED = "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
}