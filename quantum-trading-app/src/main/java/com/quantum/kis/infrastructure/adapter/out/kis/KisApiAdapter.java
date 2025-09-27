package com.quantum.kis.infrastructure.adapter.out.kis;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.application.port.out.KisTokenRepositoryPort;
import com.quantum.kis.domain.token.KisTokenId;
import com.quantum.kis.infrastructure.config.KisConfig;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;
import com.quantum.kis.dto.AccessTokenResponse;
import com.quantum.kis.dto.ChartDataResponse;
import com.quantum.kis.dto.KisTokenRequest;
import com.quantum.kis.dto.KisWebSocketRequest;
import com.quantum.kis.dto.WebSocketKeyResponse;
import com.quantum.kis.exception.KisApiException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

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
    private final KisTokenRepositoryPort kisTokenRepositoryPort;

    public KisApiAdapter(RestClient restClient, KisConfig config, ObjectMapper objectMapper,
                        KisTokenRepositoryPort kisTokenRepositoryPort) {
        this.restClient = restClient;
        this.config = config;
        this.objectMapper = objectMapper;
        this.kisTokenRepositoryPort = kisTokenRepositoryPort;
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

    @Override
    public ChartDataResponse getDailyChartData(KisEnvironment environment, String stockCode,
                                              LocalDate startDate, LocalDate endDate) {
        log.info("일봉차트 데이터 조회 시작 - 환경: {}, 종목: {}, 기간: {} ~ {}",
                environment, stockCode, startDate, endDate);

        String url = config.getRestApiUrl(environment) + "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice";
        String trId = "FHKST03010100"; // 국내주식기간별시세

        // 날짜를 YYYYMMDD 형식으로 변환
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd");
        String startDateStr = startDate.format(formatter);
        String endDateStr = endDate.format(formatter);

        try {
            String accessToken = getAccessToken(environment);

            var response = restClient.get()
                    .uri(url + "?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD=" + stockCode +
                         "&FID_INPUT_DATE_1=" + startDateStr + "&FID_INPUT_DATE_2=" + endDateStr +
                         "&FID_PERIOD_DIV_CODE=D&FID_ORG_ADJ_PRC=1")
                    .header("Content-Type", "application/json")
                    .header("authorization", "Bearer " + accessToken)
                    .header("appkey", config.getMyApp())
                    .header("appsecret", config.getMySec())
                    .header("tr_id", trId)
                    .header("custtype", "P") // 개인
                    .retrieve()
                    .body(ChartDataResponse.class);

            // curl 로깅
            logChartDataCurl(url, stockCode, startDateStr, endDateStr, accessToken);

            log.info("일봉차트 데이터 조회 성공 - 종목: {}, 데이터 건수: {}",
                    stockCode, response != null && response.output2() != null ? response.output2().size() : 0);
            return response;

        } catch (Exception e) {
            log.error("일봉차트 데이터 조회 실패 - 종목: {}, 오류: {}", stockCode, e.getMessage());
            throw new KisApiException("차트 데이터 조회 실패: " + e.getMessage(), e);
        }
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
        Object request = createRequest(environment, tokenType);
        Class<?> responseType = getResponseType(tokenType);

        try {
            var response = restClient.post()
                    .uri(url)
                    .header("Content-Type", "application/json")
                    .header("Accept", "text/plain")
                    .header("charset", "UTF-8")
                    .header("User-Agent", config.getMyAgent())
                    .body(request)
                    .retrieve()
                    .body(responseType);

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
     * 환경에 맞는 액세스 토큰을 가져온다.
     */
    private String getAccessToken(KisEnvironment environment) {
        KisTokenId tokenId = new KisTokenId(environment, TokenType.ACCESS_TOKEN);
        return kisTokenRepositoryPort.findById(tokenId)
                .filter(kisToken -> kisToken.isUsable())
                .map(kisToken -> kisToken.getToken().value())
                .orElseThrow(() -> new KisApiException("사용 가능한 액세스 토큰이 없습니다: " + environment));
    }

    /**
     * 차트 데이터 조회 curl 명령어를 로깅한다.
     */
    private void logChartDataCurl(String url, String stockCode, String startDate, String endDate, String accessToken) {
        if (log.isDebugEnabled()) {
            String curl = "curl -X GET '%s?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD=%s&FID_INPUT_DATE_1=%s&FID_INPUT_DATE_2=%s&FID_PERIOD_DIV_CODE=D&FID_ORG_ADJ_PRC=1' " +
                    "-H 'Content-Type: application/json' " +
                    "-H 'authorization: Bearer %s' " +
                    "-H 'appkey: %s' " +
                    "-H 'appsecret: %s' " +
                    "-H 'tr_id: FHKST03010100' " +
                    "-H 'custtype: P'";

            String formattedCurl = String.format(curl, url, stockCode, startDate, endDate, accessToken,
                    config.getMyApp(), config.getMySec());
            log.debug("KIS Chart API Curl: {}", formattedCurl);
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

    /**
     * 토큰 타입별로 요청 객체를 생성한다.
     */
    private Object createRequest(KisEnvironment environment, TokenType tokenType) {
        switch (tokenType) {
            case ACCESS_TOKEN:
                return KisTokenRequest.of(environment, config);
            case WEBSOCKET_KEY:
                return KisWebSocketRequest.of(environment, config);
            default:
                throw new IllegalArgumentException("Unknown token type: " + tokenType);
        }
    }

    /**
     * 토큰 타입별로 응답 타입을 반환한다.
     */
    private Class<?> getResponseType(TokenType tokenType) {
        switch (tokenType) {
            case ACCESS_TOKEN:
                return AccessTokenResponse.class;
            case WEBSOCKET_KEY:
                return WebSocketKeyResponse.class;
            default:
                throw new IllegalArgumentException("Unknown token type: " + tokenType);
        }
    }
}