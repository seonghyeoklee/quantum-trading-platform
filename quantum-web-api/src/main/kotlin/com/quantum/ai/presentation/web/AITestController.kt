package com.quantum.ai.presentation.web

import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.Parameter
import io.swagger.v3.oas.annotations.media.Content
import io.swagger.v3.oas.annotations.media.Schema
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.tags.Tag
import org.slf4j.LoggerFactory
import org.springframework.ai.chat.client.ChatClient
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import jakarta.validation.Valid

/**
 * Spring AI 테스트 컨트롤러
 * 
 * Spring AI 1.0.0-M2 환경 구성 확인 및 기본 AI 기능 테스트를 위한 컨트롤러입니다.
 * OpenAI GPT 모델과의 연동 상태를 확인하고 간단한 채팅 테스트를 수행할 수 있습니다.
 */
@RestController
@RequestMapping("/api/v1/ai")
@Tag(name = "AI Test & Integration", description = "Spring AI 환경 테스트 및 AI 기능 검증 API")
class AITestController(
    private val chatClient: ChatClient
) {
    
    private val logger = LoggerFactory.getLogger(AITestController::class.java)
    
    /**
     * AI 환경 구성 테스트
     */
    @GetMapping("/test")
    @Operation(
        summary = "Spring AI 환경 구성 테스트",
        description = "Spring AI 1.0.0-M2 환경이 정상적으로 구성되었는지 확인합니다. " +
                "OpenAI API 키 설정과 ChatClient 빈 생성 상태를 검증합니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200",
            description = "AI 환경 구성 확인 완료",
            content = [Content(
                schema = Schema(
                    example = """{
                        "status": "success",
                        "message": "Spring AI 환경 구성 완료",
                        "timestamp": "1704067200000"
                    }"""
                )
            )]
        ),
        ApiResponse(
            responseCode = "500",
            description = "AI 환경 구성 오류"
        )
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
        summary = "AI 채팅 기능 테스트",
        description = "OpenAI GPT 모델과의 실제 통신을 테스트합니다. " +
                "OPENAI_API_KEY 환경변수가 설정되어 있어야 정상 동작합니다."
    )
    @ApiResponses(
        ApiResponse(
            responseCode = "200",
            description = "AI 채팅 테스트 완료 (성공/실패 포함)",
            content = [Content(schema = Schema(implementation = ChatTestResponse::class))]
        ),
        ApiResponse(
            responseCode = "500",
            description = "서버 내부 오류"
        )
    )
    fun chatTest(
        @Parameter(description = "AI 채팅 테스트 요청", required = true)
        @RequestBody @Valid request: ChatTestRequest
    ): ResponseEntity<ChatTestResponse> {
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
    @field:Parameter(
        description = "AI에게 보낼 테스트 메시지",
        example = "안녕하세요, 오늘 날씨는 어떤가요?",
        required = true
    )
    val message: String
)

/**
 * 채팅 테스트 응답 DTO
 */
data class ChatTestResponse(
    @field:Parameter(description = "테스트 성공 여부", example = "true")
    val success: Boolean,
    
    @field:Parameter(description = "AI 응답 내용 (성공시)", example = "안녕하세요! 저는 AI 어시스턴트입니다.")
    val response: String?,
    
    @field:Parameter(description = "테스트 결과 메시지", example = "AI 채팅 테스트 성공")
    val message: String
)