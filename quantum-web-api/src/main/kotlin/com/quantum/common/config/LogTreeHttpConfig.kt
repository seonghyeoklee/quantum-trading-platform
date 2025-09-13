package com.quantum.common.config

import io.github.logtree.core.LogTree
import io.github.logtree.core.LogTreeContext
import org.slf4j.LoggerFactory
import org.springframework.context.annotation.Configuration
import org.springframework.web.servlet.HandlerInterceptor
import org.springframework.web.servlet.config.annotation.InterceptorRegistry
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/**
 * LogTree HTTP 로깅 설정
 * Logbook을 대체하여 HTTP 요청/응답을 LogTree 계층구조에 통합
 */
@Configuration
class LogTreeHttpConfig : WebMvcConfigurer {

    override fun addInterceptors(registry: InterceptorRegistry) {
        registry.addInterceptor(LogTreeHttpInterceptor())
            .excludePathPatterns(
                "/actuator/**",
                "/health",
                "/error", 
                "/favicon.ico",
                "/swagger-ui/**",
                "/v3/api-docs/**",
                "/docs/**"
            )
    }
}

/**
 * LogTree HTTP 인터셉터
 * HTTP 요청/응답을 LogTree의 계층형 구조에 포함시켜 통합 로깅
 */
class LogTreeHttpInterceptor : HandlerInterceptor {
    
    private val logger = LoggerFactory.getLogger(this::class.java)
    private val timeFormatter = DateTimeFormatter.ofPattern("HH:mm:ss.SSS")
    
    companion object {
        private const val START_TIME_ATTR = "logTreeStartTime"
        private const val TRACE_NAME_ATTR = "logTreeTraceName"
    }

    override fun preHandle(
        request: HttpServletRequest,
        response: HttpServletResponse,
        handler: Any
    ): Boolean {
        val startTime = System.currentTimeMillis()
        val timestamp = LocalDateTime.now().format(timeFormatter)
        
        // HTTP 요청 정보
        val method = request.method
        val uri = request.requestURI
        val queryString = request.queryString
        val fullUrl = if (queryString != null) "$uri?$queryString" else uri
        
        val traceName = "HTTP $method $uri"
        request.setAttribute(START_TIME_ATTR, startTime)
        request.setAttribute(TRACE_NAME_ATTR, traceName)
        
        // HTTP 요청 trace 시작 (실제 UUID trace ID 생성)
        val traceId = LogTreeContext.startTrace()
        request.setAttribute("traceId", traceId)
        
        // 요청 정보 로깅 (HTTP 요청 요약을 일반 로그로)
        logger.info("$traceName")
        
        LogTree.span("HTTP Request") {
            val requestInfo = buildString {
                append("→ $method $fullUrl")
                if (request.contentLength > 0) {
                    append(" [${request.contentLength}B]")
                }
                request.getHeader("Content-Type")?.let {
                    append(" ($it)")
                }
            }
            
            logger.info("[$timestamp] $requestInfo")
        }
        
        return true
    }

    override fun afterCompletion(
        request: HttpServletRequest,
        response: HttpServletResponse,
        handler: Any,
        ex: Exception?
    ) {
        val startTime = request.getAttribute(START_TIME_ATTR) as? Long ?: return
        
        val duration = System.currentTimeMillis() - startTime
        val timestamp = LocalDateTime.now().format(timeFormatter)
        val status = response.status
        
        // HTTP 응답 정보를 LogTree 스팬으로 완료
        LogTree.span("HTTP Response") {
            val responseInfo = buildString {
                append("← $status")
                
                // 상태 코드별 표시
                when (status) {
                    in 200..299 -> append(" ✅")
                    in 300..399 -> append(" ↩️")
                    in 400..499 -> append(" ❌")
                    in 500..599 -> append(" 🔥")
                }
                
                append(" (${duration}ms)")
                
                // Content-Length 추가
                response.getHeader("Content-Length")?.let {
                    append(" [${it}B]")
                }
                
                // 예외 정보 추가
                ex?.let {
                    append(" - Error: ${it.javaClass.simpleName}: ${it.message}")
                }
            }
            
            logger.info("[$timestamp] $responseInfo")
        }
        
        // HTTP 요청 완료 요약 로깅
        logger.info("HTTP $status (${duration}ms)")
        
        // HTTP trace 완료
        LogTreeContext.endTrace()
    }
}