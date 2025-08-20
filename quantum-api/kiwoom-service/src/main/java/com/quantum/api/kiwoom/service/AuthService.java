package com.quantum.api.kiwoom.service;

import com.quantum.api.kiwoom.config.KiwoomProperties;
import com.quantum.api.kiwoom.dto.auth.TokenRequest;
import com.quantum.api.kiwoom.dto.auth.TokenResponse;
import com.quantum.api.kiwoom.dto.auth.TokenRevokeRequest;
import com.quantum.api.kiwoom.dto.auth.CachedTokenInfo;
import com.quantum.api.kiwoom.client.KiwoomApiClient;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

/**
 * OAuth 인증 서비스
 * 키움증권 OAuth 2.0 토큰 관리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {

    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenCacheService;
    private final KiwoomProperties kiwoomProperties;

    /**
     * 키움증권 OAuth 2.0 토큰 발급 (키움 API 스펙 + 캐시 정책)
     * JSON Body: {"grant_type": "client_credentials", "appkey": "...", "secretkey": "..."}
     * 
     * 캐시 정책:
     * - 6시간 이내 재요청: 기존 토큰 재활용
     * - 6시간 후 재요청: 새 토큰 발급 + 기존 토큰 폐기
     */
    public Mono<TokenResponse> issueKiwoomOAuthToken(TokenRequest request) {
        log.info("키움증권 OAuth 토큰 발급 시작 - grant_type: {}", request.getGrantType());

        // 1. grant_type 검증
        if (!"client_credentials".equals(request.getGrantType())) {
            log.error("지원하지 않는 grant_type: {}", request.getGrantType());
            return Mono.error(new IllegalArgumentException("grant_type은 client_credentials만 지원됩니다"));
        }

        // 2. appkey, secretkey 검증
        String appkey = request.getAppkey();
        String secretkey = request.getSecretkey();

        if (appkey == null || appkey.trim().isEmpty()) {
            return Mono.error(new IllegalArgumentException("appkey는 필수입니다"));
        }

        if (secretkey == null || secretkey.trim().isEmpty()) {
            return Mono.error(new IllegalArgumentException("secretkey는 필수입니다"));
        }

        // 3. 자격증명 검증
        if (!isValidKiwoomCredentials(appkey, secretkey)) {
            return Mono.error(new IllegalArgumentException("유효하지 않은 앱키 또는 시크릿키입니다"));
        }

        // 4. 캐시된 토큰 확인 및 정책 적용
        return tokenCacheService.getCachedToken(appkey)
                .flatMap(cachedToken -> {
                    if (cachedToken == null || cachedToken.isExpired()) {
                        // 캐시된 토큰이 없거나 만료된 경우 -> 새 토큰 발급
                        log.info("새 토큰 발급 필요 - appkey: {}***, 이유: {}", 
                                appkey.substring(0, Math.min(5, appkey.length())),
                                cachedToken == null ? "캐시 없음" : "토큰 만료");
                        return generateAndCacheNewToken(appkey, secretkey);
                        
                    } else if (cachedToken.isReusable()) {
                        // 6시간 이내 발급된 토큰 -> 재활용
                        log.info("캐시된 토큰 재활용 - appkey: {}***, 발급시간: {}", 
                                appkey.substring(0, Math.min(5, appkey.length())),
                                cachedToken.getIssuedAt());
                        return Mono.just(buildTokenResponse(cachedToken));
                        
                    } else {
                        // 6시간 후 재요청 -> 새 토큰 발급 + 기존 토큰 폐기
                        log.info("토큰 갱신 필요 - appkey: {}***, 발급시간: {}", 
                                appkey.substring(0, Math.min(5, appkey.length())),
                                cachedToken.getIssuedAt());
                        return generateAndCacheNewToken(appkey, secretkey);
                    }
                })
                .switchIfEmpty(
                    // 캐시 조회 결과가 null인 경우 새 토큰 발급
                    generateAndCacheNewToken(appkey, secretkey)
                )
                .doOnNext(response -> log.info("키움 OAuth 토큰 발급 완료 - 만료시간: {}", response.getExpiresDt()))
                .onErrorMap(error -> {
                    log.error("키움 OAuth 토큰 발급 실패", error);
                    return new RuntimeException("OAuth 토큰 발급에 실패했습니다.", error);
                });
    }

    /**
     * 새 토큰 생성 및 캐시 저장
     */
    private Mono<TokenResponse> generateAndCacheNewToken(String appkey, String secretkey) {
        return Mono.fromCallable(() -> {
            // 1. 새 토큰 생성
            String accessToken = generateKiwoomAccessToken();
            LocalDateTime now = LocalDateTime.now();
            LocalDateTime expiresAt = now.plusHours(24);
            String expiresDt = expiresAt.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            
            // 2. 캐시 정보 생성
            CachedTokenInfo tokenInfo = CachedTokenInfo.builder()
                    .appkey(appkey)
                    .token(accessToken)
                    .issuedAt(now)
                    .expiresAt(expiresAt)
                    .expiresDt(expiresDt)
                    .build();
                    
            // 3. 응답 생성
            TokenResponse response = buildTokenResponse(tokenInfo);
            
            log.info("새 토큰 생성 - appkey: {}***, token: {}***, expires: {}", 
                    appkey.substring(0, Math.min(5, appkey.length())),
                    accessToken.substring(0, Math.min(8, accessToken.length())),
                    expiresDt);
            
            return response;
        })
        .flatMap(response -> {
            // 4. 캐시에 저장
            CachedTokenInfo tokenInfo = CachedTokenInfo.builder()
                    .appkey(appkey)
                    .token(response.getToken())
                    .issuedAt(LocalDateTime.now())
                    .expiresAt(LocalDateTime.now().plusHours(24))
                    .expiresDt(response.getExpiresDt())
                    .build();
                    
            return tokenCacheService.cacheToken(tokenInfo)
                    .thenReturn(response);
        });
    }
    
    /**
     * CachedTokenInfo를 TokenResponse로 변환
     */
    private TokenResponse buildTokenResponse(CachedTokenInfo tokenInfo) {
        return TokenResponse.builder()
                .expiresDt(tokenInfo.getExpiresDt())         // 키움 API 스펙
                .tokenType("bearer")                         // 공통
                .token(tokenInfo.getToken())                 // 키움 API 스펙
                .accessToken(tokenInfo.getToken())           // OAuth 2.0 호환
                .expiresIn(86400L)                          // OAuth 2.0 호환 (24시간)
                .build();
    }

    /**
     * 키움증권 OAuth 2.0 토큰 폐기 (키움 API 스펙)
     * JSON Body: {"appkey": "...", "secretkey": "...", "token": "..."}
     */
    public Mono<Void> revokeKiwoomOAuthToken(TokenRevokeRequest request) {
        log.info("키움증권 OAuth 토큰 폐기 시작 - appkey: {}", 
                request.getAppkey() != null ? request.getAppkey().substring(0, Math.min(5, request.getAppkey().length())) + "***" : "null");

        // 1. 필수 필드 검증
        String appkey = request.getAppkey();
        String secretkey = request.getSecretkey();
        String token = request.getToken();

        if (appkey == null || appkey.trim().isEmpty()) {
            return Mono.error(new IllegalArgumentException("appkey는 필수입니다"));
        }

        if (secretkey == null || secretkey.trim().isEmpty()) {
            return Mono.error(new IllegalArgumentException("secretkey는 필수입니다"));
        }

        if (token == null || token.trim().isEmpty()) {
            return Mono.error(new IllegalArgumentException("token은 필수입니다"));
        }

        // 2. 앱키/시크릿 검증
        if (!isValidKiwoomCredentials(appkey, secretkey)) {
            return Mono.error(new IllegalArgumentException("유효하지 않은 앱키 또는 시크릿키입니다"));
        }

        // 3. 토큰 검증 및 캐시에서 폐기
        return validateAndRevokeToken(token)
                .then(tokenCacheService.evictTokenByValue(token))
                .doOnSuccess(v -> log.info("키움 OAuth 토큰 폐기 성공"))
                .onErrorMap(error -> {
                    log.error("키움 OAuth 토큰 폐기 실패", error);
                    return new RuntimeException("OAuth 토큰 폐기에 실패했습니다.", error);
                });
    }

    /**
     * 접근 토큰 발급 (호환용)
     */
    public Mono<TokenResponse> getAccessToken(TokenRequest request) {
        log.info("키움증권 접근토큰 발급 시작: {}", request.getGrantType());

        return kiwoomApiClient.requestToken(request)
                .doOnNext(response -> log.info("접근토큰 발급 성공, 만료시간: {}초", response.getExpiresIn()))
                .onErrorMap(error -> {
                    log.error("접근토큰 발급 실패", error);
                    return new RuntimeException("토큰 발급에 실패했습니다.", error);
                });
    }

    /**
     * 접근 토큰 갱신
     */
    public Mono<TokenResponse> refreshAccessToken(String refreshToken) {
        log.info("접근토큰 갱신 시작");

        TokenRequest request = TokenRequest.builder()
                .grantType("refresh_token")
                .refreshToken(extractToken(refreshToken))
                .build();

        return kiwoomApiClient.requestToken(request)
                .doOnNext(response -> log.info("접근토큰 갱신 성공"))
                .onErrorMap(error -> {
                    log.error("접근토큰 갱신 실패", error);
                    return new RuntimeException("토큰 갱신에 실패했습니다.", error);
                });
    }

    /**
     * 접근 토큰 폐기
     */
    public Mono<Void> revokeToken(String accessToken) {
        log.info("접근토큰 폐기 시작");

        return kiwoomApiClient.revokeToken(extractToken(accessToken))
                .doOnSuccess(v -> log.info("접근토큰 폐기 성공"))
                .onErrorMap(error -> {
                    log.error("접근토큰 폐기 실패", error);
                    return new RuntimeException("토큰 폐기에 실패했습니다.", error);
                });
    }

    /**
     * Authorization 헤더에서 토큰 추출
     */
    private String extractToken(String authHeader) {
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        return authHeader;
    }

    /**
     * Authorization 헤더 파싱 (앱키:시크릿 Base64)
     */
    private String[] parseAuthorization(String authorization) {
        try {
            if (authorization == null || !authorization.startsWith("Bearer ")) {
                throw new IllegalArgumentException("유효하지 않은 Authorization 헤더입니다");
            }

            String encodedCredentials = authorization.substring(7); // "Bearer " 제거
            String decodedCredentials = new String(java.util.Base64.getDecoder().decode(encodedCredentials));
            String[] parts = decodedCredentials.split(":");

            if (parts.length != 2) {
                throw new IllegalArgumentException("Authorization 헤더 형식이 올바르지 않습니다 (appkey:secretkey)");
            }

            return parts; // [appkey, secretkey]
        } catch (Exception e) {
            log.error("Authorization 헤더 파싱 실패: {}", e.getMessage());
            throw new IllegalArgumentException("Authorization 헤더 파싱에 실패했습니다", e);
        }
    }

    /**
     * 키움증권 토큰 생성 (시뮬레이션)
     */
    private Mono<TokenResponse> generateKiwoomToken(String appkey, String secretkey) {
        return Mono.fromCallable(() -> {
            // 1. 앱키/시크릿 검증 (시뮬레이션)
            if (!isValidKiwoomCredentials(appkey, secretkey)) {
                throw new IllegalArgumentException("유효하지 않은 앱키 또는 시크릿키입니다");
            }

            // 2. 키움 스타일 토큰 생성 (실제 키움 API 응답과 유사하게)
            String accessToken = generateKiwoomAccessToken();

            // 3. 만료시간 계산 (24시간 후, 키움 API 스펙 형식)
            LocalDateTime expiresAt = LocalDateTime.now().plusHours(24);
            String expiresDt = expiresAt.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));

            log.info("키움 토큰 생성 성공 - appkey: {}***, expires: {}",
                    appkey.substring(0, Math.min(5, appkey.length())), expiresDt);

            // 4. 키움 API 응답 스펙에 맞는 응답 생성
            return TokenResponse.builder()
                    .expiresDt(expiresDt)         // 키움 필수: "20241107083713"
                    .tokenType("bearer")          // 키움 필수: "bearer"
                    .token(accessToken)           // 키움 필수: "WQUOywbI..."
                    // OAuth 2.0 호환 필드들 (클라이언트 호환성)
                    .accessToken(accessToken)
                    .expiresIn(86400L)
                    .build();
        });
    }

    /**
     * 키움 앱키/시크릿 검증 (실제 키 포함)
     */
    private boolean isValidKiwoomCredentials(String appkey, String secretkey) {
        // 실제 키움증권 API 키 + 테스트용 자격증명
        return java.util.Map.of(
            // 실전투자 키
            "[REDACTED_API_KEY]", "[REDACTED_SECRET]",
            // 모의투자 키
            "[REDACTED_MOCK_KEY]", "[REDACTED_MOCK_SECRET]",
            // 테스트용 키
            "AxserEsdrcdica", "S5afcLwerebDreJ4xvc",              // 키움 샘플과 유사한 형태
            "KiwoomAppKey01", "KiwoomSecretKey01",                // 테스트용
            "PSAxserEsdrcd", "PSS5afcLwerebDreJ4",               // 모의투자용
            "TestKiwoomApp", "TestKiwoomSecret2024",             // 개발용
            "DemoKiwoomKey", "DemoKiwoomSecret9999"              // 데모용
        ).getOrDefault(appkey, "").equals(secretkey);
    }

    /**
     * 키움 스타일 액세스 토큰 생성
     */
    private String generateKiwoomAccessToken() {
        // 키움 API 실제 토큰과 유사한 형태로 생성
        // 예: "WQUOywbIhknhRmbIhmhTXJcxwFdVvYxH..."
        String prefix = "WQUOywbI";  // 키움 토큰 고정 prefix
        String randomPart = java.util.UUID.randomUUID().toString().replace("-", "").substring(0, 24);
        return prefix + randomPart;
    }
    
    /**
     * 현재 모드에 따른 기본 토큰 발급 (환경변수 키 사용)
     */
    public Mono<TokenResponse> issueDefaultToken() {
        String appKey = kiwoomProperties.getCurrentAppKey();
        String appSecret = kiwoomProperties.getCurrentAppSecret();
        
        if (appKey == null || appKey.trim().isEmpty() || 
            appSecret == null || appSecret.trim().isEmpty()) {
            
            log.error("환경변수에서 키움 API 키를 찾을 수 없습니다. 모드: {}", 
                    kiwoomProperties.getModeDescription());
            return Mono.error(new IllegalStateException(
                    "키움 API 키가 설정되지 않았습니다. .env 파일을 확인해주세요."));
        }
        
        log.info("기본 토큰 발급 시작 - 모드: {}, 앱키: {}***", 
                kiwoomProperties.getModeDescription(),
                appKey.substring(0, Math.min(8, appKey.length())));
        
        TokenRequest request = TokenRequest.builder()
                .grantType("client_credentials")
                .appkey(appKey)
                .secretkey(appSecret)
                .build();
                
        return issueKiwoomOAuthToken(request);
    }

    /**
     * 토큰 검증 및 폐기 (시뮬레이션)
     */
    private Mono<Void> validateAndRevokeToken(String token) {
        return Mono.fromRunnable(() -> {
            // 1. 토큰 형식 검증 (키움 토큰은 "WQUOywbI"로 시작)
            if (!token.startsWith("WQUOywbI")) {
                throw new IllegalArgumentException("유효하지 않은 토큰 형식입니다");
            }
            
            // 2. 토큰 길이 검증 (키움 토큰은 보통 32자 이상)
            if (token.length() < 16) {
                throw new IllegalArgumentException("토큰 길이가 유효하지 않습니다");
            }
            
            // 3. 토큰 폐기 처리 (실제로는 Redis나 DB에서 토큰 제거)
            log.info("토큰 폐기 처리: {}***", token.substring(0, Math.min(8, token.length())));
            
            // 시뮬레이션: 실제로는 토큰 저장소에서 제거
            // tokenRepository.deleteByToken(token);
        });
    }
}
