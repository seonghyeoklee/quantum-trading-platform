package com.quantum.stock.application.service

import com.quantum.stock.presentation.dto.*
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.stereotype.Service
import org.springframework.web.reactive.function.client.WebClient
import org.springframework.web.reactive.function.client.awaitBody
import org.springframework.web.reactive.function.BodyInserters
import org.springframework.web.server.ResponseStatusException
import java.time.LocalDate

/**
 * DINO 테스트 비즈니스 서비스
 * 
 * KIS Adapter의 DINO API와 통신하여 AI 기반 주식 분석을 수행합니다.
 */
@Service
class DinoTestService(
    private val webClient: WebClient,
    @Value("\${kis.adapter.base-url:http://adapter.quantum-trading.com:8000}")
    private val adapterBaseUrl: String
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    /**
     * 종합 DINO 테스트 실행
     */
    suspend fun runComprehensiveDinoTest(request: ComprehensiveDinoTestRequest): ComprehensiveDinoTestResponse {
        logger.info("종합 DINO 테스트 실행 - stockCode: ${request.stockCode}, forceRerun: ${request.forceRerun}")
        
        return try {
            val requestBody = mapOf(
                "stock_code" to request.stockCode,
                "company_name" to (request.companyName ?: ""),
                "force_rerun" to request.forceRerun
            )
            
            val response = webClient
                .post()
                .uri("$adapterBaseUrl/dino-test/comprehensive")
                .contentType(MediaType.APPLICATION_JSON)
                .body(BodyInserters.fromValue(requestBody))
                .retrieve()
                .onStatus({ it.is4xxClientError }) { 
                    throw ResponseStatusException(HttpStatus.BAD_REQUEST, "종합 DINO 테스트 요청이 잘못되었습니다")
                }
                .onStatus({ it.is5xxServerError }) {
                    throw ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "DINO 테스트 서버 오류")
                }
                .awaitBody<Map<String, Any>>()
            
            logger.info("종합 DINO 테스트 완료 - stockCode: ${request.stockCode}")
            
            mapToComprehensiveDinoTestResponse(response)
            
        } catch (exception: Exception) {
            logger.error("종합 DINO 테스트 실행 오류 - stockCode: ${request.stockCode}", exception)
            throw ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, 
                "종합 DINO 테스트 중 오류가 발생했습니다: ${exception.message}")
        }
    }
    
    /**
     * 개별 재무분석 테스트 실행
     */
    suspend fun runFinanceTest(stockCode: String): DinoTestFinanceResponse {
        logger.info("재무분석 테스트 실행 - stockCode: $stockCode")
        
        return try {
            val response = webClient
                .get()
                .uri("$adapterBaseUrl/dino-test/finance/$stockCode")
                .retrieve()
                .onStatus({ it.is4xxClientError }) { 
                    throw ResponseStatusException(HttpStatus.NOT_FOUND, "종목을 찾을 수 없습니다: $stockCode")
                }
                .onStatus({ it.is5xxServerError }) {
                    throw ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "재무분석 서버 오류")
                }
                .awaitBody<Map<String, Any>>()
            
            logger.info("재무분석 테스트 완료 - stockCode: $stockCode")
            
            DinoTestFinanceResponse(
                success = response["success"] as? Boolean ?: false,
                stockCode = response["stock_code"] as? String ?: stockCode,
                score = response["score"] as? Int ?: 0,
                message = response["message"] as? String ?: "",
                rawData = response["raw_data"] as? Map<String, Any> ?: emptyMap()
            )
            
        } catch (exception: Exception) {
            logger.error("재무분석 테스트 실행 오류 - stockCode: $stockCode", exception)
            throw ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, 
                "재무분석 테스트 중 오류가 발생했습니다: ${exception.message}")
        }
    }
    
    /**
     * 개별 기술적 분석 테스트 실행
     */
    suspend fun runTechnicalTest(stockCode: String): DinoTestTechnicalResponse {
        logger.info("기술적 분석 테스트 실행 - stockCode: $stockCode")
        
        return try {
            val response = webClient
                .get()
                .uri("$adapterBaseUrl/dino-test/technical/$stockCode")
                .retrieve()
                .onStatus({ it.is4xxClientError }) { 
                    throw ResponseStatusException(HttpStatus.NOT_FOUND, "종목을 찾을 수 없습니다: $stockCode")
                }
                .onStatus({ it.is5xxServerError }) {
                    throw ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "기술적 분석 서버 오류")
                }
                .awaitBody<Map<String, Any>>()
            
            logger.info("기술적 분석 테스트 완료 - stockCode: $stockCode")
            
            DinoTestTechnicalResponse(
                success = response["success"] as? Boolean ?: false,
                stockCode = response["stock_code"] as? String ?: stockCode,
                score = response["score"] as? Int ?: 0,
                message = response["message"] as? String ?: "",
                rawData = response["raw_data"] as? Map<String, Any> ?: emptyMap()
            )
            
        } catch (exception: Exception) {
            logger.error("기술적 분석 테스트 실행 오류 - stockCode: $stockCode", exception)
            throw ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, 
                "기술적 분석 테스트 중 오류가 발생했습니다: ${exception.message}")
        }
    }
    
    /**
     * 개별 가격분석 테스트 실행
     */
    suspend fun runPriceTest(stockCode: String): DinoTestPriceResponse {
        logger.info("가격분석 테스트 실행 - stockCode: $stockCode")
        
        return try {
            val response = webClient
                .get()
                .uri("$adapterBaseUrl/dino-test/price/$stockCode")
                .retrieve()
                .onStatus({ it.is4xxClientError }) { 
                    throw ResponseStatusException(HttpStatus.NOT_FOUND, "종목을 찾을 수 없습니다: $stockCode")
                }
                .onStatus({ it.is5xxServerError }) {
                    throw ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "가격분석 서버 오류")
                }
                .awaitBody<Map<String, Any>>()
            
            logger.info("가격분석 테스트 완료 - stockCode: $stockCode")
            
            DinoTestPriceResponse(
                success = response["success"] as? Boolean ?: false,
                stockCode = response["stock_code"] as? String ?: stockCode,
                score = response["score"] as? Int ?: 0,
                message = response["message"] as? String ?: "",
                rawData = response["raw_data"] as? Map<String, Any> ?: emptyMap()
            )
            
        } catch (exception: Exception) {
            logger.error("가격분석 테스트 실행 오류 - stockCode: $stockCode", exception)
            throw ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, 
                "가격분석 테스트 중 오류가 발생했습니다: ${exception.message}")
        }
    }
    
    /**
     * 개별 소재분석 테스트 실행
     */
    suspend fun runMaterialTest(stockCode: String): DinoTestMaterialResponse {
        logger.info("소재분석 테스트 실행 - stockCode: $stockCode")
        
        return try {
            val response = webClient
                .get()
                .uri("$adapterBaseUrl/dino-test/material/$stockCode")
                .retrieve()
                .onStatus({ it.is4xxClientError }) { 
                    throw ResponseStatusException(HttpStatus.NOT_FOUND, "종목을 찾을 수 없습니다: $stockCode")
                }
                .onStatus({ it.is5xxServerError }) {
                    throw ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "소재분석 서버 오류")
                }
                .awaitBody<Map<String, Any>>()
            
            logger.info("소재분석 테스트 완료 - stockCode: $stockCode")
            
            DinoTestMaterialResponse(
                success = response["success"] as? Boolean ?: false,
                stockCode = response["stock_code"] as? String ?: stockCode,
                score = response["score"] as? Int ?: 0,
                message = response["message"] as? String ?: "",
                analysisSummary = response["analysis_summary"] as? String ?: "",
                rawData = response["raw_data"] as? Map<String, Any> ?: emptyMap()
            )
            
        } catch (exception: Exception) {
            logger.error("소재분석 테스트 실행 오류 - stockCode: $stockCode", exception)
            throw ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, 
                "소재분석 테스트 중 오류가 발생했습니다: ${exception.message}")
        }
    }
    
    /**
     * DINO 테스트 결과 조회
     */
    suspend fun getDinoTestResults(
        stockCode: String? = null,
        analysisDate: String? = null,
        limit: Int = 100
    ): DinoTestResultsResponse {
        logger.info("DINO 테스트 결과 조회 - stockCode: $stockCode, date: $analysisDate, limit: $limit")
        
        return try {
            val queryParams = mutableListOf<String>()
            stockCode?.let { queryParams.add("stock_code=$it") }
            analysisDate?.let { queryParams.add("analysis_date=$it") }
            queryParams.add("limit=$limit")
            
            val queryString = if (queryParams.isNotEmpty()) "?${queryParams.joinToString("&")}" else ""
            
            val response = webClient
                .get()
                .uri("$adapterBaseUrl/dino-test/results$queryString")
                .retrieve()
                .onStatus({ it.is5xxServerError }) {
                    throw ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "DINO 결과 조회 서버 오류")
                }
                .awaitBody<Map<String, Any>>()
            
            logger.info("DINO 테스트 결과 조회 완료")
            
            mapToDinoTestResultsResponse(response)
            
        } catch (exception: Exception) {
            logger.error("DINO 테스트 결과 조회 오류", exception)
            throw ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, 
                "DINO 테스트 결과 조회 중 오류가 발생했습니다: ${exception.message}")
        }
    }
    
    /**
     * 최신 DINO 테스트 결과 조회
     */
    suspend fun getLatestDinoTestResult(stockCode: String): DinoTestLatestResultResponse {
        logger.info("최신 DINO 테스트 결과 조회 - stockCode: $stockCode")
        
        return try {
            val response = webClient
                .get()
                .uri("$adapterBaseUrl/dino-test/results/$stockCode/latest")
                .retrieve()
                .onStatus({ it.is4xxClientError }) { 
                    throw ResponseStatusException(HttpStatus.NOT_FOUND, "종목의 DINO 테스트 결과를 찾을 수 없습니다: $stockCode")
                }
                .onStatus({ it.is5xxServerError }) {
                    throw ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "DINO 결과 조회 서버 오류")
                }
                .awaitBody<Map<String, Any>>()
            
            logger.info("최신 DINO 테스트 결과 조회 완료 - stockCode: $stockCode")
            
            mapToDinoTestLatestResultResponse(response)
            
        } catch (exception: Exception) {
            logger.error("최신 DINO 테스트 결과 조회 오류 - stockCode: $stockCode", exception)
            throw ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, 
                "최신 DINO 테스트 결과 조회 중 오류가 발생했습니다: ${exception.message}")
        }
    }
    
    // Private helper methods for mapping responses
    
    private fun mapToComprehensiveDinoTestResponse(response: Map<String, Any>): ComprehensiveDinoTestResponse {
        return ComprehensiveDinoTestResponse(
            success = response["success"] as? Boolean ?: false,
            stockCode = response["stock_code"] as? String ?: "",
            companyName = response["company_name"] as? String ?: "",
            analysisDate = response["analysis_date"] as? String ?: "",
            status = response["status"] as? String ?: "",
            financeScore = response["finance_score"] as? Int ?: 0,
            technicalScore = response["technical_score"] as? Int ?: 0,
            priceScore = response["price_score"] as? Int ?: 0,
            materialScore = response["material_score"] as? Int ?: 0,
            eventScore = response["event_score"] as? Int ?: 0,
            themeScore = response["theme_score"] as? Int ?: 0,
            positiveNewsScore = response["positive_news_score"] as? Int ?: 0,
            interestCoverageScore = response["interest_coverage_score"] as? Int ?: 0,
            totalScore = response["total_score"] as? Int ?: 0,
            analysisGrade = response["analysis_grade"] as? String ?: "D",
            message = response["message"] as? String ?: ""
        )
    }
    
    private fun mapToDinoTestResultsResponse(response: Map<String, Any>): DinoTestResultsResponse {
        val results = (response["results"] as? List<Map<String, Any>> ?: emptyList()).map { result ->
            mapToDinoTestResultDto(result)
        }
        
        return DinoTestResultsResponse(
            success = response["success"] as? Boolean ?: false,
            results = results,
            totalCount = response["total_count"] as? Int ?: 0,
            message = response["message"] as? String ?: ""
        )
    }
    
    private fun mapToDinoTestLatestResultResponse(response: Map<String, Any>): DinoTestLatestResultResponse {
        val resultData = response["result"] as? Map<String, Any>
        val result = resultData?.let { mapToDinoTestResultDto(it) }
        
        return DinoTestLatestResultResponse(
            success = response["success"] as? Boolean ?: false,
            result = result,
            message = response["message"] as? String ?: ""
        )
    }
    
    private fun mapToDinoTestResultDto(result: Map<String, Any>): DinoTestResultDto {
        return DinoTestResultDto(
            id = (result["id"] as? Number)?.toLong() ?: 0L,
            stockCode = result["stock_code"] as? String ?: "",
            companyName = result["company_name"] as? String ?: "",
            analysisDate = result["analysis_date"] as? String ?: "",
            status = result["status"] as? String ?: "",
            financeScore = result["finance_score"] as? Int ?: 0,
            technicalScore = result["technical_score"] as? Int ?: 0,
            priceScore = result["price_score"] as? Int ?: 0,
            materialScore = result["material_score"] as? Int ?: 0,
            eventScore = result["event_score"] as? Int ?: 0,
            themeScore = result["theme_score"] as? Int ?: 0,
            positiveNewsScore = result["positive_news_score"] as? Int ?: 0,
            interestCoverageScore = result["interest_coverage_score"] as? Int ?: 0,
            totalScore = result["total_score"] as? Int ?: 0,
            analysisGrade = result["analysis_grade"] as? String ?: "D",
            createdAt = result["created_at"] as? String ?: "",
            updatedAt = result["updated_at"] as? String ?: "",
            rawData = result["raw_data"] as? Map<String, Any> ?: emptyMap()
        )
    }
}