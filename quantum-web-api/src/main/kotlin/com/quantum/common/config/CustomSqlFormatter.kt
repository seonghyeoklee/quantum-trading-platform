package com.quantum.common.config

import com.p6spy.engine.spy.appender.MessageFormattingStrategy
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** SQL 로깅을 한 줄로 깔끔하게 포맷팅 */
class CustomSqlFormatter : MessageFormattingStrategy {

    override fun formatMessage(
            connectionId: Int,
            now: String?,
            elapsed: Long,
            category: String?,
            prepared: String?,
            sql: String?,
            url: String?
    ): String {
        val timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss.SSS"))
        val cleanSql = sql?.replace(Regex("\\s+"), " ")?.trim() ?: ""

        return "[$timestamp] 🗄️  ${elapsed}ms | $cleanSql"
    }
}
