package com.quantum.ai.presentation.web

import org.slf4j.LoggerFactory
import org.springframework.ai.chat.client.ChatClient
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

/**
 * Spring AI 테스트 컨트롤러
 * 기본 AI 환경 구성 확인용
 */
@RestController
@RequestMapping("/api/v1/ai")
class AITestController(
    private val chatClient: ChatClient
) {
    
    private val logger = LoggerFactory.getLogger(AITestController::class.java)
    
    /**
     * AI 환경 구성 테스트
     */
    @GetMapping("/test")
    fun testAI(): ResponseEntity<Map<String, String>> {
        logger.info("AI 환경 테스트 요청")
        
        val response = mapOf(
            "status" to "success",
            "message" to "Spring AI 환경 구성 완료",
            "timestamp" to System.currentTimeMillis().toString()
        )
        
        return ResponseEntity.ok(response)
    }
    
    /**
     * 간단한 AI 채팅 테스트 (API 키 필요)
     */
    @PostMapping("/chat")
    fun chatTest(@RequestBody request: ChatTestRequest): ResponseEntity<ChatTestResponse> {
        return try {
            logger.info("AI 채팅 테스트 요청: {}", request.message)
            
            // Spring AI 1.0.0-M2 새로운 API 사용
            val response = chatClient.prompt()
                .user(request.message)
                .call()
                .content()
            
            logger.info("AI 응답: {}", response)
            
            ResponseEntity.ok(
                ChatTestResponse(
                    success = true,
                    response = response,
                    message = "AI 채팅 테스트 성공"
                )
            )
            
        } catch (exception: Exception) {
            logger.error("AI 채팅 테스트 실패", exception)
            
            ResponseEntity.ok(
                ChatTestResponse(
                    success = false,
                    response = null,
                    message = "AI 채팅 테스트 실패: ${exception.message}"
                )
            )
        }
    }
}

/**
 * 채팅 테스트 요청 DTO
 */
data class ChatTestRequest(
    val message: String
)

/**
 * 채팅 테스트 응답 DTO
 */
data class ChatTestResponse(
    val success: Boolean,
    val response: String?,
    val message: String
)