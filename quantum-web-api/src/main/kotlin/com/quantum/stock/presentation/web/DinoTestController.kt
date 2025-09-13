package com.quantum.stock.presentation.web

import com.quantum.stock.application.service.DinoTestService
import com.quantum.stock.presentation.dto.*
import org.slf4j.LoggerFactory
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import kotlinx.coroutines.runBlocking

/**
 * DINO 테스트 API 컨트롤러
 * 
 * AI 기반 주식 분석 시스템(DINO) 테스트 관련 API 제공
 */
@RestController
@RequestMapping("/api/v1/dino-test")
@CrossOrigin(origins = ["http://quantum-trading.com:3000", "http://localhost:3000"])
class DinoTestController(
    private val dinoTestService: DinoTestService
) {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    
    /**
     * 종합 DINO 테스트 실행
     */
    @PostMapping("/comprehensive")
    fun runComprehensiveDinoTest(@RequestBody request: ComprehensiveDinoTestRequest): ResponseEntity<ComprehensiveDinoTestResponse> {
        
        return try {
            logger.info("종합 DINO 테스트 요청 - stockCode: ${request.stockCode}")
            
            // 종목코드 유효성 검증
            if (!request.stockCode.matches(Regex("^[A-Z0-9]{6}$"))) {
                logger.warn("유효하지 않은 종목코드 형식: ${request.stockCode}")
                return ResponseEntity.badRequest().build()
            }
            
            val result = runBlocking {
                dinoTestService.runComprehensiveDinoTest(request)
            }
            
            logger.info("종합 DINO 테스트 완료 - ${result.companyName}: 총점 ${result.totalScore}점")
            
            ResponseEntity.ok(result)
            
        } catch (exception: Exception) {
            logger.error("종합 DINO 테스트 실행 실패 - stockCode: ${request.stockCode}", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * 개별 재무분석 테스트 실행
     */
    @PostMapping("/finance/{stockCode}")
    fun runFinanceTest(@PathVariable stockCode: String): ResponseEntity<DinoTestFinanceResponse> {
        
        return try {
            logger.info("재무분석 테스트 요청 - stockCode: $stockCode")
            
            // 종목코드 유효성 검증
            if (!stockCode.matches(Regex("^[A-Z0-9]{6}$"))) {
                logger.warn("유효하지 않은 종목코드 형식: $stockCode")
                return ResponseEntity.badRequest().build()
            }
            
            val result = runBlocking {
                dinoTestService.runFinanceTest(stockCode)
            }
            
            logger.info("재무분석 테스트 완료 - stockCode: $stockCode, 점수: ${result.score}점")
            
            ResponseEntity.ok(result)
            
        } catch (exception: Exception) {
            logger.error("재무분석 테스트 실행 실패 - stockCode: $stockCode", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * 개별 기술적 분석 테스트 실행
     */
    @PostMapping("/technical/{stockCode}")
    fun runTechnicalTest(@PathVariable stockCode: String): ResponseEntity<DinoTestTechnicalResponse> {
        
        return try {
            logger.info("기술적 분석 테스트 요청 - stockCode: $stockCode")
            
            // 종목코드 유효성 검증
            if (!stockCode.matches(Regex("^[A-Z0-9]{6}$"))) {
                logger.warn("유효하지 않은 종목코드 형식: $stockCode")
                return ResponseEntity.badRequest().build()
            }
            
            val result = runBlocking {
                dinoTestService.runTechnicalTest(stockCode)
            }
            
            logger.info("기술적 분석 테스트 완료 - stockCode: $stockCode, 점수: ${result.score}점")
            
            ResponseEntity.ok(result)
            
        } catch (exception: Exception) {
            logger.error("기술적 분석 테스트 실행 실패 - stockCode: $stockCode", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * 개별 가격분석 테스트 실행
     */
    @PostMapping("/price/{stockCode}")
    fun runPriceTest(@PathVariable stockCode: String): ResponseEntity<DinoTestPriceResponse> {
        
        return try {
            logger.info("가격분석 테스트 요청 - stockCode: $stockCode")
            
            // 종목코드 유효성 검증
            if (!stockCode.matches(Regex("^[A-Z0-9]{6}$"))) {
                logger.warn("유효하지 않은 종목코드 형식: $stockCode")
                return ResponseEntity.badRequest().build()
            }
            
            val result = runBlocking {
                dinoTestService.runPriceTest(stockCode)
            }
            
            logger.info("가격분석 테스트 완료 - stockCode: $stockCode, 점수: ${result.score}점")
            
            ResponseEntity.ok(result)
            
        } catch (exception: Exception) {
            logger.error("가격분석 테스트 실행 실패 - stockCode: $stockCode", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * 개별 소재분석 테스트 실행
     */
    @PostMapping("/material/{stockCode}")
    fun runMaterialTest(@PathVariable stockCode: String): ResponseEntity<DinoTestMaterialResponse> {
        
        return try {
            logger.info("소재분석 테스트 요청 - stockCode: $stockCode")
            
            // 종목코드 유효성 검증
            if (!stockCode.matches(Regex("^[A-Z0-9]{6}$"))) {
                logger.warn("유효하지 않은 종목코드 형식: $stockCode")
                return ResponseEntity.badRequest().build()
            }
            
            val result = runBlocking {
                dinoTestService.runMaterialTest(stockCode)
            }
            
            logger.info("소재분석 테스트 완료 - stockCode: $stockCode, 점수: ${result.score}점")
            
            ResponseEntity.ok(result)
            
        } catch (exception: Exception) {
            logger.error("소재분석 테스트 실행 실패 - stockCode: $stockCode", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * DINO 테스트 결과 전체 조회
     */
    @GetMapping("/results")
    fun getDinoTestResults(
        @RequestParam(required = false) stockCode: String?,
        @RequestParam(required = false) analysisDate: String?,
        @RequestParam(defaultValue = "100") limit: Int
    ): ResponseEntity<DinoTestResultsResponse> {
        
        return try {
            logger.info("DINO 테스트 결과 조회 - stockCode: $stockCode, date: $analysisDate, limit: $limit")
            
            // limit 유효성 검증 (최대 1000개)
            val validLimit = minOf(limit, 1000)
            
            val result = runBlocking {
                dinoTestService.getDinoTestResults(stockCode, analysisDate, validLimit)
            }
            
            logger.info("DINO 테스트 결과 조회 완료 - 조회된 결과: ${result.results.size}개")
            
            ResponseEntity.ok(result)
            
        } catch (exception: Exception) {
            logger.error("DINO 테스트 결과 조회 실패", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * 특정 종목의 최신 DINO 테스트 결과 조회
     */
    @GetMapping("/results/{stockCode}/latest")
    fun getLatestDinoTestResult(@PathVariable stockCode: String): ResponseEntity<DinoTestLatestResultResponse> {
        
        return try {
            logger.info("최신 DINO 테스트 결과 조회 - stockCode: $stockCode")
            
            // 종목코드 유효성 검증
            if (!stockCode.matches(Regex("^[A-Z0-9]{6}$"))) {
                logger.warn("유효하지 않은 종목코드 형식: $stockCode")
                return ResponseEntity.badRequest().build()
            }
            
            val result = runBlocking {
                dinoTestService.getLatestDinoTestResult(stockCode)
            }
            
            ResponseEntity.ok(result)
            
        } catch (exception: Exception) {
            logger.error("최신 DINO 테스트 결과 조회 실패 - stockCode: $stockCode", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * DINO 테스트 실행 상태 조회 (실시간 모니터링용)
     */
    @GetMapping("/status/{stockCode}")
    fun getDinoTestExecutionStatus(@PathVariable stockCode: String): ResponseEntity<Map<String, DinoTestExecutionStatus>> {
        
        return try {
            logger.info("DINO 테스트 실행 상태 조회 - stockCode: $stockCode")
            
            // 종목코드 유효성 검증
            if (!stockCode.matches(Regex("^[A-Z0-9]{6}$"))) {
                logger.warn("유효하지 않은 종목코드 형식: $stockCode")
                return ResponseEntity.badRequest().build()
            }
            
            // Mock 데이터 반환 (향후 실제 구현)
            val statuses = mapOf(
                "finance" to DinoTestExecutionStatus("finance", "idle", 0),
                "technical" to DinoTestExecutionStatus("technical", "idle", 0),
                "price" to DinoTestExecutionStatus("price", "idle", 0),
                "material" to DinoTestExecutionStatus("material", "idle", 0),
                "event" to DinoTestExecutionStatus("event", "idle", 0),
                "theme" to DinoTestExecutionStatus("theme", "idle", 0),
                "positive_news" to DinoTestExecutionStatus("positive_news", "idle", 0),
                "interest_coverage" to DinoTestExecutionStatus("interest_coverage", "idle", 0)
            )
            
            logger.info("DINO 테스트 실행 상태 조회 완료 - stockCode: $stockCode")
            
            ResponseEntity.ok(statuses)
            
        } catch (exception: Exception) {
            logger.error("DINO 테스트 실행 상태 조회 실패 - stockCode: $stockCode", exception)
            ResponseEntity.internalServerError().build()
        }
    }
    
    /**
     * 헬스체크 엔드포인트
     */
    @GetMapping("/health")
    fun healthCheck(): ResponseEntity<Map<String, Any>> {
        logger.info("DINO 테스트 헬스체크 요청")
        
        val response = mapOf(
            "status" to "healthy",
            "service" to "dino-test-api",
            "timestamp" to System.currentTimeMillis(),
            "version" to "1.0.0"
        )
        
        return ResponseEntity.ok(response)
    }
}