package com.quantum.common.config

import io.swagger.v3.oas.models.OpenAPI
import io.swagger.v3.oas.models.info.Info
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

/**
 * OpenAPI/Swagger 간단 설정
 */
@Configuration
class OpenApiConfig {

    @Bean
    fun openAPI(): OpenAPI {
        return OpenAPI()
            .info(
                Info()
                    .title("Quantum Trading Platform API")
                    .description("Korea Investment & Securities API를 활용한 자동 거래 플랫폼")
                    .version("v1.0.0")
            )
    }
}