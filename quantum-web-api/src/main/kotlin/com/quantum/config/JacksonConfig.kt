package com.quantum.config

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.databind.DeserializationFeature
import com.fasterxml.jackson.databind.SerializationFeature
import com.fasterxml.jackson.module.kotlin.KotlinModule
import com.fasterxml.jackson.core.StreamWriteConstraints
import com.fasterxml.jackson.core.StreamReadConstraints
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.context.annotation.Primary

/**
 * Jackson 설정 클래스
 * - JSON 직렬화/역직렬화 설정
 * - 중첩 깊이 제한 완화
 * - Kotlin 지원
 */
@Configuration
class JacksonConfig {

    @Bean
    @Primary
    fun objectMapper(): ObjectMapper {
        return ObjectMapper().apply {
            // Kotlin 모듈 등록
            registerModule(KotlinModule.Builder().build())
            
            // Java Time 모듈 등록 (LocalDateTime 지원)
            registerModule(JavaTimeModule())
            
            // 직렬화 설정
            configure(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS, false)
            configure(SerializationFeature.FAIL_ON_EMPTY_BEANS, false)
            
            // 역직렬화 설정
            configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
            configure(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES, false)
            
            // 스트림 제약 설정 - 중첩 깊이 및 문자열 길이 제한 완화
            factory.setStreamWriteConstraints(
                StreamWriteConstraints.builder()
                    .maxNestingDepth(2000)  // 기본 1000 → 2000으로 증가
                    .build()
            )
                
            factory.setStreamReadConstraints(
                StreamReadConstraints.builder()
                    .maxNestingDepth(2000)  // 기본 1000 → 2000으로 증가
                    .maxStringLength(50_000_000)  // 문자열 길이 제한 완화
                    .maxNumberLength(10000)  // 숫자 길이 제한 완화
                    .build()
            )
        }
    }
}