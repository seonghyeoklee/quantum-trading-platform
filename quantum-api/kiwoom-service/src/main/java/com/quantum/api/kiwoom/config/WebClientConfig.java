package com.quantum.api.kiwoom.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.ExchangeFilterFunction;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

/**
 * WebClient 설정
 * 키움증권 API 호출용 WebClient 구성
 */
@Configuration
@RequiredArgsConstructor
@Slf4j
public class WebClientConfig {
    
    private final KiwoomProperties kiwoomProperties;
    
    /**
     * 키움증권 API용 WebClient (현재 모드에 따라 자동 선택)
     */
    @Bean
    public WebClient kiwoomWebClient() {
        String baseUrl = kiwoomProperties.getCurrentBaseUrl();
        int timeout = kiwoomProperties.getTimeout();
        
        log.info("키움증권 WebClient 초기화 - 모드: {}, URL: {}", 
                kiwoomProperties.getModeDescription(), baseUrl);
        
        // HTTP 클라이언트 설정
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, timeout)
                .responseTimeout(Duration.ofMillis(timeout))
                .doOnConnected(conn ->
                        conn.addHandlerLast(new ReadTimeoutHandler(timeout, TimeUnit.MILLISECONDS))
                            .addHandlerLast(new WriteTimeoutHandler(timeout, TimeUnit.MILLISECONDS)));
        
        return WebClient.builder()
                .baseUrl(baseUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .filter(logRequest())
                .filter(logResponse())
                .build();
    }
    
    /**
     * 실전투자 전용 WebClient (명시적 사용)
     */
    @Bean
    public WebClient prodWebClient() {
        String baseUrl = kiwoomProperties.getBaseUrl();
        
        log.info("실전투자 WebClient 초기화 - URL: {}", baseUrl);
        
        return WebClient.builder()
                .baseUrl(baseUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
                .filter(logRequest())
                .filter(logResponse())
                .build();
    }
    
    /**
     * 모의투자 전용 WebClient (명시적 사용)
     */
    @Bean
    public WebClient mockWebClient() {
        String mockUrl = kiwoomProperties.getMockUrl();
        
        log.info("모의투자 WebClient 초기화 - URL: {}", mockUrl);
        
        return WebClient.builder()
                .baseUrl(mockUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
                .filter(logRequest())
                .filter(logResponse())
                .build();
    }
    
    /**
     * 요청 로깅 필터
     */
    private ExchangeFilterFunction logRequest() {
        return ExchangeFilterFunction.ofRequestProcessor(clientRequest -> {
            if (log.isDebugEnabled()) {
                StringBuilder sb = new StringBuilder("Request: ");
                sb.append(clientRequest.method()).append(" ").append(clientRequest.url());
                
                clientRequest.headers().forEach((name, values) -> {
                    // 민감한 정보는 마스킹
                    if ("authorization".equalsIgnoreCase(name)) {
                        sb.append("\n").append(name).append(": Bearer ***");
                    } else {
                        values.forEach(value -> sb.append("\n").append(name).append(": ").append(value));
                    }
                });
                
                log.debug(sb.toString());
            }
            return Mono.just(clientRequest);
        });
    }
    
    /**
     * 응답 로깅 필터
     */
    private ExchangeFilterFunction logResponse() {
        return ExchangeFilterFunction.ofResponseProcessor(clientResponse -> {
            if (log.isDebugEnabled()) {
                StringBuilder sb = new StringBuilder("Response: ");
                sb.append(clientResponse.statusCode());
                
                clientResponse.headers().asHttpHeaders().forEach((name, values) -> {
                    values.forEach(value -> sb.append("\n").append(name).append(": ").append(value));
                });
                
                log.debug(sb.toString());
            }
            return Mono.just(clientResponse);
        });
    }
}