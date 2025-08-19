package com.quantum.api.kiwoom.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
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
@Slf4j
public class WebClientConfig {
    
    @Value("${kiwoom.api.base-url:https://api.kiwoom.com}")
    private String kiwoomBaseUrl;
    
    @Value("${kiwoom.api.timeout:30000}")
    private int timeout;
    
    /**
     * 키움증권 API용 WebClient
     */
    @Bean
    public WebClient kiwoomWebClient() {
        // HTTP 클라이언트 설정
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, timeout)
                .responseTimeout(Duration.ofMillis(timeout))
                .doOnConnected(conn ->
                        conn.addHandlerLast(new ReadTimeoutHandler(timeout, TimeUnit.MILLISECONDS))
                            .addHandlerLast(new WriteTimeoutHandler(timeout, TimeUnit.MILLISECONDS)));
        
        return WebClient.builder()
                .baseUrl(kiwoomBaseUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .filter(logRequest())
                .filter(logResponse())
                .build();
    }
    
    /**
     * 모의투자용 WebClient
     */
    @Bean
    public WebClient mockWebClient() {
        return WebClient.builder()
                .baseUrl("https://mockapi.kiwoom.com")
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