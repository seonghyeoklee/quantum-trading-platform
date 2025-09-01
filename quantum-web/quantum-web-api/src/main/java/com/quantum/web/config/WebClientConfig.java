package com.quantum.web.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.ExchangeFilterFunction;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

/**
 * WebClient 설정
 * 
 * RestTemplate을 대체하여 사용하는 비동기 HTTP 클라이언트 설정
 * - Netty 기반 HTTP 클라이언트
 * - Connection Timeout, Read/Write Timeout 설정
 * - 로깅 및 에러 핸들링
 */
@Configuration
@Slf4j
public class WebClientConfig {

    @Value("${app.webclient.connect-timeout:5000}")
    private int connectTimeout;

    @Value("${app.webclient.read-timeout:30000}")
    private int readTimeout;

    @Value("${app.webclient.write-timeout:30000}")
    private int writeTimeout;

    @Value("${app.webclient.max-memory-size:10485760}")
    private int maxMemorySize; // 10MB

    /**
     * 기본 WebClient Bean
     */
    @Bean
    public WebClient webClient() {
        return WebClient.builder()
                .clientConnector(new ReactorClientHttpConnector(httpClient()))
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(maxMemorySize))
                .filter(logRequest())
                .filter(logResponse())
                .filter(errorHandlingFilter())
                .build();
    }

    /**
     * 키움증권 API 전용 WebClient Bean
     */
    @Bean("kiwoomWebClient")
    public WebClient kiwoomWebClient() {
        return WebClient.builder()
                .clientConnector(new ReactorClientHttpConnector(httpClient()))
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(maxMemorySize))
                .filter(logRequest())
                .filter(logResponse())
                .filter(errorHandlingFilter())
                .defaultHeader("Content-Type", "application/json")
                .defaultHeader("Accept", "application/json")
                .build();
    }

    /**
     * HTTP 클라이언트 설정
     */
    private HttpClient httpClient() {
        return HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, connectTimeout)
                .responseTimeout(Duration.ofMillis(readTimeout))
                .doOnConnected(conn -> 
                    conn.addHandlerLast(new ReadTimeoutHandler(readTimeout, TimeUnit.MILLISECONDS))
                        .addHandlerLast(new WriteTimeoutHandler(writeTimeout, TimeUnit.MILLISECONDS))
                );
    }

    /**
     * 요청 로깅 필터
     */
    private ExchangeFilterFunction logRequest() {
        return ExchangeFilterFunction.ofRequestProcessor(clientRequest -> {
            if (log.isDebugEnabled()) {
                log.debug("WebClient Request: {} {}", clientRequest.method(), clientRequest.url());
                clientRequest.headers().forEach((name, values) -> 
                    log.debug("WebClient Header: {} = {}", name, values)
                );
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
                log.debug("WebClient Response Status: {}", clientResponse.statusCode());
                clientResponse.headers().asHttpHeaders().forEach((name, values) ->
                    log.debug("WebClient Response Header: {} = {}", name, values)
                );
            }
            return Mono.just(clientResponse);
        });
    }

    /**
     * 에러 핸들링 필터
     */
    private ExchangeFilterFunction errorHandlingFilter() {
        return ExchangeFilterFunction.ofResponseProcessor(clientResponse -> {
            if (clientResponse.statusCode().isError()) {
                log.warn("WebClient Error Response: {}", 
                    clientResponse.statusCode().value());
            }
            return Mono.just(clientResponse);
        });
    }
}