package com.quantum.stock.presentation.dto

import com.fasterxml.jackson.annotation.JsonProperty
import java.time.LocalDate

/**
 * DINO 테스트 관련 DTO 클래스들
 * 
 * KIS Adapter의 DINO API 응답과 매핑됩니다.
 */

/**
 * 종합 DINO 테스트 요청 DTO
 */
data class ComprehensiveDinoTestRequest(
    val stockCode: String,
    val companyName: String? = null,
    val forceRerun: Boolean = false
)

/**
 * 종합 DINO 테스트 응답 DTO
 */
data class ComprehensiveDinoTestResponse(
    val success: Boolean,
    val stockCode: String,
    val companyName: String,
    val analysisDate: String,
    val status: String,
    
    // 8개 영역별 점수
    val financeScore: Int,
    val technicalScore: Int,
    val priceScore: Int,
    val materialScore: Int,
    val eventScore: Int,
    val themeScore: Int,
    val positiveNewsScore: Int,
    val interestCoverageScore: Int,
    
    // 총점 및 등급
    val totalScore: Int,
    val analysisGrade: String,
    
    val message: String
)

/**
 * 개별 DINO 테스트 응답 기본 클래스
 */
abstract class BaseDinoTestResponse(
    open val success: Boolean,
    open val stockCode: String,
    open val score: Int,
    open val message: String
)

/**
 * 재무분석 테스트 응답 DTO
 */
data class DinoTestFinanceResponse(
    override val success: Boolean,
    override val stockCode: String,
    override val score: Int,
    override val message: String,
    val rawData: Map<String, Any> = emptyMap()
) : BaseDinoTestResponse(success, stockCode, score, message)

/**
 * 기술적 분석 테스트 응답 DTO
 */
data class DinoTestTechnicalResponse(
    override val success: Boolean,
    override val stockCode: String,
    override val score: Int,
    override val message: String,
    val rawData: Map<String, Any> = emptyMap()
) : BaseDinoTestResponse(success, stockCode, score, message)

/**
 * 가격분석 테스트 응답 DTO
 */
data class DinoTestPriceResponse(
    override val success: Boolean,
    override val stockCode: String,
    override val score: Int,
    override val message: String,
    val rawData: Map<String, Any> = emptyMap()
) : BaseDinoTestResponse(success, stockCode, score, message)

/**
 * 소재분석 테스트 응답 DTO
 */
data class DinoTestMaterialResponse(
    override val success: Boolean,
    override val stockCode: String,
    override val score: Int,
    override val message: String,
    val analysisSummary: String = "",
    val rawData: Map<String, Any> = emptyMap()
) : BaseDinoTestResponse(success, stockCode, score, message)

/**
 * 이벤트분석 테스트 응답 DTO
 */
data class DinoTestEventResponse(
    override val success: Boolean,
    override val stockCode: String,
    override val score: Int,
    override val message: String,
    val analysisSummary: String = "",
    val rawData: Map<String, Any> = emptyMap()
) : BaseDinoTestResponse(success, stockCode, score, message)

/**
 * 테마분석 테스트 응답 DTO
 */
data class DinoTestThemeResponse(
    override val success: Boolean,
    override val stockCode: String,
    override val score: Int,
    override val message: String,
    val analysisSummary: String = "",
    val rawData: Map<String, Any> = emptyMap()
) : BaseDinoTestResponse(success, stockCode, score, message)

/**
 * 호재뉴스 분석 테스트 응답 DTO
 */
data class DinoTestPositiveNewsResponse(
    override val success: Boolean,
    override val stockCode: String,
    override val score: Int,
    override val message: String,
    val analysisSummary: String = "",
    val rawData: Map<String, Any> = emptyMap()
) : BaseDinoTestResponse(success, stockCode, score, message)

/**
 * 이자보상배율 분석 테스트 응답 DTO
 */
data class DinoTestInterestCoverageResponse(
    override val success: Boolean,
    override val stockCode: String,
    override val score: Int,
    override val message: String,
    val dataQuality: String = "",
    val rawData: Map<String, Any> = emptyMap()
) : BaseDinoTestResponse(success, stockCode, score, message)

/**
 * DINO 테스트 결과 조회 응답 DTO
 */
data class DinoTestResultsResponse(
    val success: Boolean,
    val results: List<DinoTestResultDto>,
    val totalCount: Int,
    val message: String
)

/**
 * DINO 테스트 결과 개별 항목 DTO
 */
data class DinoTestResultDto(
    val id: Long,
    val stockCode: String,
    val companyName: String,
    val analysisDate: String,
    val status: String,
    
    // 개별 점수들
    val financeScore: Int,
    val technicalScore: Int,
    val priceScore: Int,
    val materialScore: Int,
    val eventScore: Int,
    val themeScore: Int,
    val positiveNewsScore: Int,
    val interestCoverageScore: Int,
    
    // 총점 및 등급
    val totalScore: Int,
    val analysisGrade: String,
    
    val createdAt: String,
    val updatedAt: String,
    
    // 분석 원시 데이터
    val rawData: Map<String, Any> = emptyMap()
)

/**
 * DINO 테스트 최신 결과 응답 DTO
 */
data class DinoTestLatestResultResponse(
    val success: Boolean,
    val result: DinoTestResultDto?,
    val message: String
)

/**
 * DINO 테스트 실행 상태 DTO
 */
data class DinoTestExecutionStatus(
    val testType: String,
    val status: String, // 'idle', 'running', 'completed', 'failed'
    val progress: Int,
    val startTime: String? = null,
    val endTime: String? = null,
    val duration: Long? = null,
    val logs: List<String> = emptyList(),
    val result: DinoTestResultSummary? = null
)

/**
 * DINO 테스트 결과 요약 DTO
 */
data class DinoTestResultSummary(
    val score: Int,
    val maxScore: Int,
    val details: Map<String, Any> = emptyMap()
)