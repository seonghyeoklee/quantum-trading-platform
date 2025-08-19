package com.quantum.api.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.web.SecurityFilterChain;

/** Spring Security 설정 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http.csrf(AbstractHttpConfigurer::disable)
                .authorizeHttpRequests(
                        auth ->
                                auth
                                        // 모니터링 및 헬스체크 경로 허용
                                        .requestMatchers("/actuator/**")
                                        .permitAll()
                                        .requestMatchers("/health")
                                        .permitAll()
                                        .requestMatchers("/metrics")
                                        .permitAll()

                                        // Prometheus 메트릭 경로 허용
                                        .requestMatchers("/prometheus")
                                        .permitAll()
                                        .requestMatchers("/actuator/prometheus")
                                        .permitAll()

                                        // API 문서 경로 허용
                                        .requestMatchers("/swagger-ui/**")
                                        .permitAll()
                                        .requestMatchers("/swagger-ui.html")
                                        .permitAll()
                                        .requestMatchers("/v3/api-docs/**")
                                        .permitAll()
                                        .requestMatchers("/api-docs/**")
                                        .permitAll()
                                        .requestMatchers("/swagger-resources/**")
                                        .permitAll()
                                        .requestMatchers("/webjars/**")
                                        .permitAll()

                                        // 정적 리소스 허용
                                        .requestMatchers("/favicon.ico")
                                        .permitAll()
                                        .requestMatchers("/error")
                                        .permitAll()

                                        // 루트 경로 허용 (Swagger 리다이렉트)
                                        .requestMatchers("/")
                                        .permitAll()
                                        .requestMatchers("/api")
                                        .permitAll()

                                        // 개발용 임시 허용 (추후 인증 구현시 제거)
                                        .requestMatchers("/api/v1/**")
                                        .permitAll()

                                        // 나머지는 인증 필요
                                        .anyRequest()
                                        .authenticated())
                .build();
    }
}
