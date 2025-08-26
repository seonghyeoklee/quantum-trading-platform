package com.quantum.web.service;

import com.quantum.trading.platform.query.service.KiwoomAccountQueryService;
import com.quantum.trading.platform.query.view.KiwoomAccountView;
import com.quantum.trading.platform.shared.value.ApiCredentials;
import com.quantum.trading.platform.shared.value.EncryptedValue;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * 키움증권 API 호출 서비스
 * 
 * 암호화된 API 키를 복호화하여 실제 키움증권 API를 호출하는 서비스
 * - 암호화된 credentials 복호화
 * - 토큰 발급 및 갱신
 * - API 호출 프록시
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class KiwoomApiService {

    private final KiwoomAccountQueryService kiwoomAccountQueryService;
    private final EncryptionService encryptionService;
    private final KiwoomTokenService tokenService;
    private final RestTemplate restTemplate = new RestTemplate();

    private static final String KIWOOM_API_BASE_URL = "https://openapi.koreainvestment.com:9443";
    private static final String KIWOOM_SANDBOX_URL = "https://openapivts.koreainvestment.com:29443";

    /**
     * 사용자의 키움증권 API 토큰 발급 (복호화 사용)
     */
    public String issueKiwoomToken(String userId) {
        try {
            log.info("Issuing Kiwoom API token for user: {}", userId);

            // 1. 사용자의 키움증권 계정 정보 조회
            Optional<KiwoomAccountView> accountOpt = kiwoomAccountQueryService.getUserKiwoomAccount(userId);
            if (accountOpt.isEmpty()) {
                throw new KiwoomApiException("User has no Kiwoom account");
            }

            KiwoomAccountView account = accountOpt.get();

            // 2. 암호화된 API credentials 복호화
            // 실제 DB 필드명에 맞게 수정
            String encryptedData = account.getEncryptedClientId() + ":" + account.getEncryptedClientSecret();
            String salt = account.getEncryptionSalt();
            
            EncryptedValue encryptedCredentials = new EncryptedValue(
                    encryptedData,
                    salt
            );

            ApiCredentials credentials = encryptionService.decryptApiCredentials(encryptedCredentials);

            log.info("Successfully decrypted API credentials for user: {}", userId);

            // 3. 키움증권 OAuth 토큰 발급 API 호출
            String tokenUrl = KIWOOM_API_BASE_URL + "/oauth2/tokenP";
            
            Map<String, String> tokenRequest = new HashMap<>();
            tokenRequest.put("grant_type", "client_credentials");
            tokenRequest.put("appkey", credentials.getClientId());
            tokenRequest.put("appsecret", credentials.getClientSecret());

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, String>> request = new HttpEntity<>(tokenRequest, headers);
            
            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    tokenUrl,
                    HttpMethod.POST,
                    request,
                    (Class<Map<String, Object>>) (Class<?>) Map.class
            );

            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                Map<String, Object> tokenResponse = response.getBody();
                String accessToken = (String) tokenResponse.get("access_token");
                Long expiresIn = Long.valueOf(tokenResponse.get("expires_in").toString());

                // 4. 토큰을 Redis에 캐싱
                KiwoomTokenService.KiwoomToken token = KiwoomTokenService.KiwoomToken.builder()
                        .accessToken(accessToken)
                        .tokenType("Bearer")
                        .expiresIn(expiresIn)
                        .build();

                tokenService.storeToken(userId, account.getKiwoomAccountId(), token);

                log.info("Successfully issued and cached Kiwoom token for user: {}", userId);
                return accessToken;
            }

            throw new KiwoomApiException("Failed to issue Kiwoom token");

        } catch (Exception e) {
            log.error("Failed to issue Kiwoom token for user: {}", userId, e);
            throw new KiwoomApiException("Token issuance failed", e);
        }
    }

    /**
     * 키움증권 API 호출 (토큰 사용)
     */
    public Map<String, Object> callKiwoomApi(String userId, String endpoint, Map<String, Object> params) {
        try {
            log.debug("Calling Kiwoom API endpoint: {} for user: {}", endpoint, userId);

            // 1. 사용자의 키움증권 계정 정보 조회
            Optional<KiwoomAccountView> accountOpt = kiwoomAccountQueryService.getUserKiwoomAccount(userId);
            if (accountOpt.isEmpty()) {
                throw new KiwoomApiException("User has no Kiwoom account");
            }

            String kiwoomAccountId = accountOpt.get().getKiwoomAccountId();

            // 2. Redis에서 캐시된 토큰 조회
            Optional<String> tokenOpt = tokenService.getToken(userId, kiwoomAccountId);
            String accessToken;

            if (tokenOpt.isEmpty()) {
                // 토큰이 없으면 새로 발급
                log.info("No cached token found, issuing new token for user: {}", userId);
                accessToken = issueKiwoomToken(userId);
            } else {
                accessToken = tokenOpt.get();
            }

            // 3. 키움증권 API 호출
            String apiUrl = KIWOOM_API_BASE_URL + endpoint;

            HttpHeaders headers = new HttpHeaders();
            headers.setBearerAuth(accessToken);
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            // 복호화된 App Key/Secret도 헤더에 추가 (키움 API 요구사항)
            KiwoomAccountView account = accountOpt.get();
            String encryptedData = account.getEncryptedClientId() + ":" + account.getEncryptedClientSecret();
            String salt = account.getEncryptionSalt();
            
            EncryptedValue encryptedCredentials = new EncryptedValue(
                    encryptedData,
                    salt
            );
            ApiCredentials credentials = encryptionService.decryptApiCredentials(encryptedCredentials);
            
            headers.add("appkey", credentials.getClientId());
            headers.add("appsecret", credentials.getClientSecret());
            headers.add("tr_id", (String) params.getOrDefault("tr_id", "FHKST01010100"));

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(params, headers);

            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    apiUrl,
                    HttpMethod.POST,
                    request,
                    (Class<Map<String, Object>>) (Class<?>) Map.class
            );

            log.debug("Successfully called Kiwoom API endpoint: {} for user: {}", endpoint, userId);
            return response.getBody();

        } catch (Exception e) {
            log.error("Failed to call Kiwoom API endpoint: {} for user: {}", endpoint, userId, e);
            throw new KiwoomApiException("API call failed", e);
        }
    }

    /**
     * 주식 현재가 조회 예제
     */
    public Map<String, Object> getStockPrice(String userId, String stockCode) {
        Map<String, Object> params = new HashMap<>();
        params.put("FID_INPUT_ISCD", stockCode);
        params.put("tr_id", "FHKST01010100");

        return callKiwoomApi(userId, "/uapi/domestic-stock/v1/quotations/inquire-price", params);
    }

    /**
     * 주문 실행 예제
     */
    public Map<String, Object> placeOrder(String userId, String stockCode, int quantity, int price, String orderType) {
        Map<String, Object> params = new HashMap<>();
        params.put("CANO", "계좌번호"); // 실제 계좌번호 필요
        params.put("ACNT_PRDT_CD", "01"); // 계좌상품코드
        params.put("PDNO", stockCode); // 종목코드
        params.put("ORD_DVSN", orderType); // 주문구분
        params.put("ORD_QTY", String.valueOf(quantity)); // 주문수량
        params.put("ORD_UNPR", String.valueOf(price)); // 주문단가
        params.put("tr_id", "TTTC0802U"); // 매수 주문

        return callKiwoomApi(userId, "/uapi/domestic-stock/v1/trading/order-cash", params);
    }

    // Exception classes
    public static class KiwoomApiException extends RuntimeException {
        public KiwoomApiException(String message) {
            super(message);
        }

        public KiwoomApiException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}