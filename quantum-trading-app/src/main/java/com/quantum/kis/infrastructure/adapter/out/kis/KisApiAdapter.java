package com.quantum.kis.infrastructure.adapter.out.kis;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.infrastructure.config.KisConfig;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;
import com.quantum.kis.dto.AccessTokenResponse;
import com.quantum.kis.dto.WebSocketKeyResponse;
import com.quantum.kis.exception.KisApiException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/**
 * KIS API 어댑터
 * 외부 KIS API와의 통신을 담당하는 Infrastructure 어댑터
 */
@Component
public class KisApiAdapter implements KisApiPort {

    private static final Logger log = LoggerFactory.getLogger(KisApiAdapter.class);

    private final RestClient restClient;
    private final KisConfig config;
    private final ObjectMapper objectMapper;

    public KisApiAdapter(RestClient restClient, KisConfig config, ObjectMapper objectMapper) {
        this.restClient = restClient;
        this.config = config;
        this.objectMapper = objectMapper;
    }

    @Override
    public AccessTokenResponse issueAccessToken(KisEnvironment environment) {
        log.info("액세스 토큰 발급 시작 - 환경: {}", environment);
        return issueToken(environment, TokenType.ACCESS_TOKEN);
    }

    @Override
    public WebSocketKeyResponse issueWebSocketKey(KisEnvironment environment) {
        log.info("웹소켓 키 발급 시작 - 환경: {}", environment);
        return issueToken(environment, TokenType.WEBSOCKET_KEY);
    }

    /**
     * 제네릭 토큰 발급 메서드
     * @param environment KIS 환경
     * @param tokenType 토큰 타입
     * @param <T> 응답 타입
     * @return 토큰 응답
     */
    @SuppressWarnings("unchecked")
    private <T> T issueToken(KisEnvironment environment, TokenType tokenType) {
        String url = config.getRestApiUrl(environment) + tokenType.getEndpoint();
        Object request = tokenType.createRequest(environment, config);

        try {
            var response = restClient.post()
                    .uri(url)
                    .header("Content-Type", "application/json")
                    .header("Accept", "text/plain")
                    .header("charset", "UTF-8")
                    .header("User-Agent", config.getMyAgent())
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

                String formattedCurl = String.format(curl, url, config.getMyAgent(), jsonBody);
                log.debug("KIS API Curl: {}", formattedCurl);
            } catch (Exception e) {
                log.debug("Curl 로깅 실패: {}", e.getMessage());
            }
        }
    }
}