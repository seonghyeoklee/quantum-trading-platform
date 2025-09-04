package com.quantum.ai.presentation.web

import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.tags.Tag
import org.slf4j.LoggerFactory
import org.springframework.ai.chat.ChatClient
import org.springframework.ai.chat.ChatResponse
import org.springframework.ai.chat.messages.UserMessage
import org.springframework.ai.chat.prompt.Prompt
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

/**
 * Spring AI 테스트 컨트롤러
 * 기본 AI 환경 구성 확인용
 */
@RestController
@RequestMapping("/api/v1/ai")
@Tag(name = "AI Test", description = "Spring AI 테스트 API")
class AITestController(
    private val chatClient: ChatClient
) {
    
    private val logger = LoggerFactory.getLogger(AITestController::class.java)
    
    /**
     * AI 환경 구성 테스트
     */
    @GetMapping("/test")
    @Operation(
        summary = "AI 환경 테스트",
        description = "Spring AI 환경 구성이 정상적으로 완료되었는지 확인합니다."
    )
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
    @Operation(
        summary = "AI 채팅 테스트",
        description = "간단한 텍스트로 AI와 채팅을 테스트합니다. (OpenAI API 키 필요)"
    )
    fun chatTest(@RequestBody request: ChatTestRequest): ResponseEntity<ChatTestResponse> {
        return try {
            logger.info("AI 채팅 테스트 요청: {}", request.message)
            
            // Spring AI 0.8.1 방식으로 수정
            val userMessage = UserMessage(request.message)
            val prompt = Prompt(listOf(userMessage))
            val chatResponse: ChatResponse = chatClient.call(prompt)
            
            val aiResponse = chatResponse.result?.output?.content ?: "응답이 없습니다."
            
            logger.info("AI 응답: {}", aiResponse)
            
            ResponseEntity.ok(
                ChatTestResponse(
                    success = true,
                    response = aiResponse,
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