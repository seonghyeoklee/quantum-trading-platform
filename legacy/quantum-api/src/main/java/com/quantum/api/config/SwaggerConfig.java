package com.quantum.api.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** Swagger/OpenAPI 설정 */
@Configuration
public class SwaggerConfig {

    @Value("${server.port:8080}")
    private String serverPort;

    @Bean
    public OpenAPI quantumTradingOpenAPI() {
        return new OpenAPI()
                .info(
                        new Info()
                                .title("Quantum Trading API")
                                .description("주식 자동 매매 시스템 REST API")
                                .version("1.0.0")
                                .license(
                                        new License()
                                                .name("MIT License")
                                                .url("https://opensource.org/licenses/MIT")))
                .servers(
                        List.of(
                                new Server()
                                        .url("http://localhost:" + serverPort)
                                        .description("로컬 개발 서버"),
                                new Server()
                                        .url("https://api.quantum-trading.com")
                                        .description("운영 서버 (예정)")));
    }
}
