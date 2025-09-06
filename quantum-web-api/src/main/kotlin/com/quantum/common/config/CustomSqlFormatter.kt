package com.quantum.common.config

import com.p6spy.engine.spy.appender.MessageFormattingStrategy
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** SQL 로깅을 한 줄로 깔끔하게 포맷팅 - 중복 제거 */
class CustomSqlFormatter : MessageFormattingStrategy {
    
    companion object {
        private val recentQueries = mutableMapOf<String, Long>()
        private const val DUPLICATE_THRESHOLD_MS = 100L // 100ms 내 같은 쿼리는 중복으로 간주
    }

    override fun formatMessage(
            connectionId: Int,
            now: String?,
            elapsed: Long,
            category: String?,
            prepared: String?,
            sql: String?,
            url: String?
    ): String {
        // 빈 SQL이나 null인 경우 무시
        if (sql.isNullOrBlank()) return ""
        
        val cleanSql = sql.replace(Regex("\\s+"), " ").trim()
        val currentTime = System.currentTimeMillis()
        
        // 중복 쿼리 체크 (100ms 내 같은 쿼리)
        val lastTime = recentQueries[cleanSql]
        if (lastTime != null && (currentTime - lastTime) < DUPLICATE_THRESHOLD_MS) {
            return "" // 중복 쿼리는 무시
        }
        
        // 쿼리 기록 업데이트 (메모리 누수 방지를 위해 최대 100개만 유지)
        recentQueries[cleanSql] = currentTime
        if (recentQueries.size > 100) {
            val oldestKey = recentQueries.entries.minByOrNull { it.value }?.key
            oldestKey?.let { recentQueries.remove(it) }
        }
        
        val timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"))
        return "[$timestamp] 🗄️  ${elapsed}ms | $cleanSql"
    }
}
