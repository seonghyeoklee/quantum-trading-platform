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
                // WebSocket 제거됨

                // Swagger/OpenAPI 문서 (개발환경에서만)
                .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()

                // 관리자 전용 엔드포인트
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")

                // 매니저 이상 권한 필요
                .requestMatchers("/api/v1/portfolios/**").hasAnyRole("ADMIN", "MANAGER")
                .requestMatchers("/api/v1/trading/orders/**").hasAnyRole("ADMIN", "MANAGER", "TRADER")

                // 차트 데이터는 모든 인증된 사용자
                .requestMatchers("/api/v1/charts/**").authenticated()

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

        // 허용할 Origin (프론트엔드 URL)
        configuration.setAllowedOrigins(Arrays.asList(
            "http://localhost:3000",    // Next.js 개발 서버 (기본)
            "http://localhost:3001",    // Next.js 개발 서버 (현재 사용)
            "http://127.0.0.1:3000",    // localhost 대안
            "http://127.0.0.1:3001"     // localhost 대안
        ));

        // 허용할 HTTP 메서드
        configuration.setAllowedMethods(Arrays.asList(
            "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"
        ));

        // 허용할 헤더
        configuration.setAllowedHeaders(Arrays.asList("*")); // 모든 헤더 허용 (개발환경)

        // 인증정보 포함 허용
        configuration.setAllowCredentials(true);

        // 캐시 시간 (preflight 요청)
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);

        return source;
    }
}
