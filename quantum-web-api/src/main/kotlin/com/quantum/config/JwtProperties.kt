package com.quantum.config

import org.springframework.boot.context.properties.ConfigurationProperties
import org.springframework.stereotype.Component

/**
 * JWT 설정 프로퍼티
 */
@Component
@ConfigurationProperties(prefix = "jwt")
data class JwtProperties(
    var secret: String = "default-secret",
    var expiration: Long = 86400 // 24 hours in seconds
)