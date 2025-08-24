package com.quantum.web.config;

import com.quantum.web.security.JwtAuthenticationEntryPoint;
import com.quantum.web.security.JwtAuthenticationFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

/**
 * Spring Security Configuration
 *
 * JWT 기반 인증/인가 시스템 설정
 * - 관리자 전용 웹 애플리케이션 보안
 * - Role 기반 접근 제어 (ADMIN, MANAGER, TRADER)
 * - CORS 설정 및 WebSocket 보안
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthenticationEntryPoint jwtAuthenticationEntryPoint;
    private final JwtAuthenticationFilter jwtAuthenticationFilter;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            // CSRF 비활성화 (JWT 사용)
            .csrf(csrf -> csrf.disable())
            
            // Frame Options 설정 (기본값 유지)
            // .headers(headers -> headers.frameOptions().disable()) // 테스트 시에만 필요

            // CORS 설정
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))

            // 세션 관리 - Stateless
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))

            // 예외 처리
            .exceptionHandling(exceptions ->
                exceptions.authenticationEntryPoint(jwtAuthenticationEntryPoint))

            // 요청별 인가 설정
            .authorizeHttpRequests(authz -> authz
                // 공개 엔드포인트
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/api/health").permitAll()
                .requestMatchers("/error").permitAll() // Spring Boot 기본 오류 처리 경로
                
                // H2 Console 접근 허용 (테스트환경에서만)
                // .requestMatchers("/h2-console/**").permitAll() // 테스트 시에만 필요
                
                // Actuator 엔드포인트 허용 (개발환경에서만)
                .requestMatchers("/actuator/**").permitAll()
                
                // Swagger/OpenAPI 문서 (개발환경에서만)
                .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()

                // 관리자 전용 엔드포인트
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")

                // 매니저 이상 권한 필요
                .requestMatchers("/api/v1/portfolios/**").hasAnyRole("ADMIN", "MANAGER")
                .requestMatchers("/api/v1/trading/orders/**").hasAnyRole("ADMIN", "MANAGER", "TRADER")

                // 차트 데이터는 모든 인증된 사용자
                .requestMatchers("/api/v1/charts/**").authenticated()
                
                // 실시간 데이터는 모든 인증된 사용자
                .requestMatchers("/api/v1/realtime/**").authenticated()
                
                // WebSocket 연결
                .requestMatchers("/ws/**").permitAll() // WebSocket 연결은 별도 인증

                // 나머지 모든 요청은 인증 필요
                .anyRequest().authenticated()
            )

            // JWT 필터 추가
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();

        // 개발 환경: 모든 Origin 허용
        configuration.setAllowedOriginPatterns(Arrays.asList("*")); // 모든 Origin 허용

        // 허용할 HTTP 메서드 - 모든 메서드 허용
        configuration.setAllowedMethods(Arrays.asList(
            "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE"
        ));

        // 허용할 헤더 - 모든 헤더 허용
        configuration.setAllowedHeaders(Arrays.asList("*"));
        
        // 노출할 헤더 - 모든 헤더 허용
        configuration.setExposedHeaders(Arrays.asList("*"));

        // 인증정보 포함 허용
        configuration.setAllowCredentials(true);

        // 캐시 시간 (preflight 요청) - 더 길게 설정
        configuration.setMaxAge(86400L); // 24시간

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);

        return source;
    }
}
