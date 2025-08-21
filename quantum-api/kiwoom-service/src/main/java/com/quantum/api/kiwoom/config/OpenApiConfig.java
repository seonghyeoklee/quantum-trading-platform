package com.quantum.api.kiwoom.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import io.swagger.v3.oas.models.tags.Tag;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

/**
 * SpringDoc OpenAPI 설정
 * Spring Boot 3 + WebFlux 환경에서의 API 문서 설정
 */
@Configuration
public class OpenApiConfig {

    @Value("${server.port:8100}")
    private String serverPort;

    @Bean
    public OpenAPI kiwoomApiOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Kiwoom Securities API Service")
                        .description("""
                                키움증권 Open API 통합 서비스

                                ## 주요 기능
                                - 🔐 OAuth 2.0 토큰 관리 (자동 캐싱)
                                - 📈 주식 시세 조회 (현재가, 호가, 차트)
                                - 📊 업종 정보 조회 (업종현재가, 업종별주가, 전업종지수)
                                - 📋 종목 정보 조회 (기본정보, 검색)
                                - 💹 차트 데이터 조회 (일봉, 분봉, 주봉, 년봉, 틱)
                                - 📈 기술적 분석 (투자자기관별, 거래원매물대분석)

                                ## API 사용법
                                1. **토큰 발급**: POST `/api/auth/token` - 키움 API 키로 토큰 발급
                                2. **종목 조회**: GET `/api/stocks/{symbol}` - 종목 기본정보
                                3. **차트 조회**: GET `/api/charts/daily/{symbol}` - 일봉 차트
                                4. **업종 조회**: GET `/api/sectors/current/{sectorCode}` - 업종현재가

                                ## 환경 설정
                                - **실전투자 모드**: `KIWOOM_MODE=production`
                                - **모의투자 모드**: `KIWOOM_MODE=mock`
                                """)
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("Quantum Trading Platform")
                                .email("admin@quantum-trading.com")
                                .url("https://quantum-trading.com"))
                        .license(new License()
                                .name("MIT License")
                                .url("https://opensource.org/licenses/MIT")))
                .servers(List.of(
                        new Server()
                                .url("http://localhost:" + serverPort)
                                .description("개발 서버"),
                        new Server()
                                .url("https://api.quantum-trading.com")
                                .description("운영 서버")));
    }
}
