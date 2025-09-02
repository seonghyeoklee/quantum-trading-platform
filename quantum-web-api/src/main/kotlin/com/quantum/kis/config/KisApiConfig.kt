package com.quantum.kis.config

import org.springframework.cache.CacheManager
import org.springframework.cache.annotation.EnableCaching
import org.springframework.cache.concurrent.ConcurrentMapCacheManager
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.scheduling.annotation.EnableAsync
import org.springframework.scheduling.annotation.EnableScheduling
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor
import java.util.concurrent.Executor

/**
 * KIS API 관련 스프링 설정
 * 
 * - 캐시 설정: Rate Limit 상태 캐시
 * - 비동기 실행: API 로그 기록
 * - 스케줄링: 큐 처리
 */
@Configuration
@EnableCaching
@EnableAsync
@EnableScheduling
class KisApiConfig {
    
    /**
     * Rate Limit 상태 캐시용 단기 캐시 매니저
     * TTL: 1초 (Rate Limit 주기와 동기화)
     */
    @Bean("shortTermCacheManager")
    fun shortTermCacheManager(): CacheManager {
        val cacheManager = ConcurrentMapCacheManager()
        // 캐시 이름 등록
        cacheManager.setCacheNames(listOf("rate-limit-status"))
        return cacheManager
    }
    
    /**
     * API 로그 기록용 비동기 실행자
     * 코어 스레드: 2개, 최대 스레드: 10개
     */
    @Bean("apiLogExecutor")
    fun apiLogExecutor(): Executor {
        return ThreadPoolTaskExecutor().apply {
            corePoolSize = 2
            maxPoolSize = 10
            queueCapacity = 500
            setThreadNamePrefix("KisApiLog-")
            setWaitForTasksToCompleteOnShutdown(true)
            setAwaitTerminationSeconds(30)
            initialize()
        }
    }
    
    /**
     * 일반 비동기 작업용 실행자
     */
    @Bean("taskExecutor")
    fun taskExecutor(): Executor {
        return ThreadPoolTaskExecutor().apply {
            corePoolSize = 5
            maxPoolSize = 20
            queueCapacity = 1000
            setThreadNamePrefix("KisAsync-")
            setWaitForTasksToCompleteOnShutdown(true)
            setAwaitTerminationSeconds(60)
            initialize()
        }
    }
}