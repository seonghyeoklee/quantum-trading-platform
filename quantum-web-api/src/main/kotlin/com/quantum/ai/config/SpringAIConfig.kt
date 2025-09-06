package com.quantum.ai.config

import org.springframework.ai.chat.client.ChatClient
import org.springframework.ai.openai.OpenAiChatModel
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

/**
 * Spring AI 설정
 * Spring AI 1.0.0-M2 버전 기준
 */
@Configuration
class SpringAIConfig {

    /**
     * ChatClient 빈 설정
     */
    @Bean
    fun chatClient(openAiChatModel: OpenAiChatModel): ChatClient {
        return ChatClient.builder(openAiChatModel)
            .build()
    }
}