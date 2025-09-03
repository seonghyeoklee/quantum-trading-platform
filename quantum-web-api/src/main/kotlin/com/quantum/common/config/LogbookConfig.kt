package com.quantum.common.config

import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.context.annotation.Profile
import org.zalando.logbook.*
import org.zalando.logbook.core.DefaultSink
import org.zalando.logbook.json.JsonHttpLogFormatter

@Configuration
class LogbookConfig {

    @Bean
    @Profile("!production") // 개발 환경에서만 사용
    fun logbook(): Logbook {
        return Logbook.builder()
                .sink(
                        DefaultSink(
                                JsonHttpLogFormatter(), // JSON 형태
                                CustomHttpLogWriter() // 커스텀 로그 작성기
                        )
                )
                .build()
    }
}

/** 개발용 커스텀 HTTP 로그 작성기 요청과 응답을 한 줄로 깔끔하게 출력 */
class CustomHttpLogWriter : HttpLogWriter {

    override fun isActive(): Boolean = true

    override fun write(precorrelation: Precorrelation, request: String) {
        // Logbook이 이미 포맷된 요청 문자열을 제공
        val timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"))
        println("[$timestamp] → $request")
    }

    override fun write(correlation: Correlation, response: String) {
        // Logbook이 이미 포맷된 응답 문자열을 제공
        val timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"))
        println("[$timestamp] ← $response")
    }
}
