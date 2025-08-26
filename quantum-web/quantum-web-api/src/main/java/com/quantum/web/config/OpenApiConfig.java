package com.quantum.web.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.servers.Server;
import io.swagger.v3.oas.models.Components;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

/**
 * OpenAPI 3.0 (Swagger) 설정
 * 
 * 키움증권 계정 관리 API를 포함한 전체 REST API 문서화
 */
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(apiInfo())
                .servers(List.of(
                        new Server().url("http://localhost:8080").description("Local Development Server"),
                        new Server().url("https://api.quantum-trading.local").description("Local Production Server")
                ))
                .components(new Components()
                        .addSecuritySchemes("bearerAuth", new SecurityScheme()
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("JWT Bearer Token Authentication")))
                .addSecurityItem(new SecurityRequirement().addList("bearerAuth"));
    }

    private Info apiInfo() {
        return new Info()
                .title("Quantum Trading Platform API")
                .description("""
                        ## 키움증권 자동매매 플랫폼 REST API
                        
                        CQRS/Event Sourcing 아키텍처 기반의 주식 자동매매 플랫폼 API입니다.
                        
                        ### 주요 기능
                        - **사용자 인증**: JWT 기반 인증 시스템
                        - **키움증권 계정 관리**: API 키 암호화 저장 및 토큰 관리
                        - **주식 거래**: CQRS 패턴 기반 주문 처리
                        - **포트폴리오 관리**: 실시간 포지션 및 수익률 추적
                        - **실시간 차트**: 키움증권 OpenAPI 연동
                        
                        ### 인증 방법
                        1. `/api/v1/auth/login`으로 로그인하여 JWT 토큰 획득
                        2. Authorization 헤더에 `Bearer {token}` 형식으로 토큰 전송
                        3. 토큰 만료 시 `/api/v1/auth/refresh`로 토큰 갱신
                        
                        ### API 버전 정책
                        - **v1**: 현재 안정 버전
                        - 하위 호환성을 보장하며, 주요 변경 시 새 버전으로 분리
                        
                        ### 에러 응답 형식
                        ```json
                        {
                          "success": false,
                          "message": "Error description",
                          "data": null,
                          "timestamp": "2024-01-20T10:30:00.000Z",
                          "path": "/api/v1/..."
                        }
                        ```
                        
                        ### 키움증권 계정 관리
                        - 사용자별 키움증권 API 키 관리 (AES-256 암호화)
                        - Redis 기반 토큰 캐싱 및 자동 갱신
                        - 관리자용 계정 통계 및 관리 기능
                        
                        ### Rate Limiting
                        - 키움증권 API: 초당 5회, 분당 200회
                        - 일반 API: 초당 100회, 분당 1000회
                        """)
                .version("1.0.0")
                .contact(new Contact()
                        .name("Quantum Trading Platform Team")
                        .email("support@quantum-trading.local")
                        .url("https://github.com/quantum-trading/platform"))
                .license(new License()
                        .name("MIT License")
                        .url("https://opensource.org/licenses/MIT"));
    }
}