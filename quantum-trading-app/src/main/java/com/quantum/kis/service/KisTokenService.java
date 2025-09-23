package com.quantum.kis.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.quantum.kis.config.KisConfig;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;
import com.quantum.kis.dto.AccessTokenResponse;
import com.quantum.kis.dto.WebSocketKeyResponse;
import com.quantum.kis.exception.KisApiException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

/**
 * KIS 토큰 발급 서비스
 */
@Service
public class KisTokenService {

    private static final Logger log = LoggerFactory.getLogger(KisTokenService.class);

    private final RestClient restClient;
    private final KisConfig config;
    private final ObjectMapper objectMapper;

    public KisTokenService(RestClient restClient, KisConfig config, ObjectMapper objectMapper) {
        this.restClient = restClient;
        this.config = config;
        this.objectMapper = objectMapper;
    }

    /**
     * 제네릭 토큰 발급 메서드
     * @param environment KIS 환경
     * @param tokenType 토큰 타입
     * @param <T> 응답 타입
     * @return 토큰 응답
     */
    @SuppressWarnings("unchecked")
    public <T> T issueToken(KisEnvironment environment, TokenType tokenType) {
        String url = config.getRestApiUrl(environment) + tokenType.getEndpoint();
        Object request = tokenType.createRequest(environment, config);

        try {
            var response = restClient.post()
                    .uri(url)
                    .header("Content-Type", "application/json")
                    .header("Accept", "text/plain")
                    .header("charset", "UTF-8")
                    .header("User-Agent", config.myAgent())
                    .body(request)
                    .retrieve()
                    .body(tokenType.getResponseType());

            // curl 로깅
            logCurlCommand(url, request);

            log.info("KIS 토큰 발급 성공 - 환경: {}, 타입: {}", environment, tokenType);
            return (T) response;

        } catch (Exception e) {
            log.error("KIS 토큰 발급 실패 - 환경: {}, 타입: {}, 오류: {}",
                    environment, tokenType, e.getMessage());
            throw new KisApiException("토큰 발급 실패: " + e.getMessage(), e);
        }
    }

    /**
     * 액세스 토큰 발급
     * @param env KIS 환경
     * @return 액세스 토큰 응답
     */
    public AccessTokenResponse getAccessToken(KisEnvironment env) {
        log.info("액세스 토큰 발급 시작 - 환경: {}", env);
        return issueToken(env, TokenType.ACCESS_TOKEN);
    }

    /**
     * 웹소켓 키 발급
     * @param env KIS 환경
     * @return 웹소켓 키 응답
     */
    public WebSocketKeyResponse getWebSocketKey(KisEnvironment env) {
        log.info("웹소켓 키 발급 시작 - 환경: {}", env);
        return issueToken(env, TokenType.WEBSOCKET_KEY);
    }

    /**
     * curl 명령어를 로깅한다.
     * @param url 요청 URL
     * @param body 요청 바디
     */
    private void logCurlCommand(String url, Object body) {
        if (log.isDebugEnabled()) {
            try {
                String jsonBody = objectMapper.writeValueAsString(body);
                String curl = "curl -X POST '%s' " +
                        "-H 'Content-Type: application/json' " +
                        "-H 'Accept: text/plain' " +
                        "-H 'charset: UTF-8' " +
                        "-H 'User-Agent: %s' " +
                        "-d '%s'";

                String formattedCurl = String.format(curl, url, config.myAgent(), jsonBody);
                log.debug("KIS API Curl: {}", formattedCurl);
            } catch (Exception e) {
                log.debug("Curl 로깅 실패: {}", e.getMessage());
            }
        }
    }
}