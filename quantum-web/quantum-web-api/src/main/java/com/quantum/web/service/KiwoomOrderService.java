package com.quantum.web.service;

import com.quantum.web.dto.TradingSignalDto;
import com.quantum.web.dto.OrderExecutionResultDto;
import com.quantum.web.dto.KiwoomAuthInfo;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientException;
import reactor.core.publisher.Mono;
import org.springframework.beans.factory.annotation.Qualifier;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 키움증권 실제 주문 처리 서비스
 * 
 * Java 백엔드에서 Python 키움 어댑터로 실제 주문을 전송하는 서비스
 */
@Slf4j
@Service
public class KiwoomOrderService {
    
    private final WebClient kiwoomWebClient;
    private final KiwoomTokenService kiwoomTokenService;
    
    public KiwoomOrderService(@Qualifier("kiwoomWebClient") WebClient kiwoomWebClient,
                             KiwoomTokenService kiwoomTokenService) {
        this.kiwoomWebClient = kiwoomWebClient;
        this.kiwoomTokenService = kiwoomTokenService;
    }
    
    @Value("${kiwoom.adapter.url:http://localhost:10201}")
    private String kiwoomAdapterUrl;
    
    @Value("${kiwoom.order.timeout:30000}")
    private int orderTimeoutMs;
    
    @Value("${kiwoom.order.retry-attempts:3}")
    private int retryAttempts;
    
    /**
     * 매매신호를 키움 API 주문으로 실행
     * 
     * @param signal 매매신호
     * @param quantity 주문 수량
     * @return 주문 실행 결과
     */
    public OrderExecutionResultDto executeOrder(TradingSignalDto signal, Integer quantity) {
        log.info("키움 주문 실행 시작: {} {} {}주 @{}원", 
                signal.getSymbol(), 
                signal.getSignalType(), 
                quantity, 
                signal.getCurrentPrice());
        
        // 주문 타입에 따른 처리
        switch (signal.getSignalType()) {
            case "BUY":
                return executeBuyOrder(signal, quantity);
            case "SELL":
            case "CLOSE":
                return executeSellOrder(signal, quantity);
            default:
                return OrderExecutionResultDto.rejected(signal, 
                    "지원하지 않는 주문 타입: " + signal.getSignalType());
        }
    }
    
    /**
     * 매수 주문 실행
     * 
     * @param signal 매매신호
     * @param quantity 수량
     * @return 실행 결과
     */
    private OrderExecutionResultDto executeBuyOrder(TradingSignalDto signal, Integer quantity) {
        try {
            // 키움 매수 주문 요청 구성
            Map<String, Object> orderRequest = createBuyOrderRequest(signal, quantity);
            
            // 키움 어댑터로 주문 전송
            Map<String, Object> response = sendOrderToKiwoom(orderRequest, "buy", signal);
            
            return parseKiwoomResponse(signal, quantity, response, "BUY");
            
        } catch (Exception e) {
            log.error("매수 주문 실행 실패: {}", e.getMessage(), e);
            return OrderExecutionResultDto.failure(signal, 
                "매수 주문 실행 실패: " + e.getMessage(), 
                "BUY_ORDER_FAILED");
        }
    }
    
    /**
     * 매도 주문 실행
     * 
     * @param signal 매매신호
     * @param quantity 수량
     * @return 실행 결과
     */
    private OrderExecutionResultDto executeSellOrder(TradingSignalDto signal, Integer quantity) {
        try {
            // 키움 매도 주문 요청 구성
            Map<String, Object> orderRequest = createSellOrderRequest(signal, quantity);
            
            // 키움 어댑터로 주문 전송
            Map<String, Object> response = sendOrderToKiwoom(orderRequest, "sell", signal);
            
            return parseKiwoomResponse(signal, quantity, response, "SELL");
            
        } catch (Exception e) {
            log.error("매도 주문 실행 실패: {}", e.getMessage(), e);
            return OrderExecutionResultDto.failure(signal, 
                "매도 주문 실행 실패: " + e.getMessage(), 
                "SELL_ORDER_FAILED");
        }
    }
    
    /**
     * 키움 매수 주문 요청 생성 (Python API StockBuyOrderRequest 스펙) - 헤더 기반
     * 
     * @param signal 매매신호
     * @param quantity 수량
     * @return 주문 요청 데이터 (Python API 형식, 인증 정보는 헤더로 전달)
     */
    private Map<String, Object> createBuyOrderRequest(TradingSignalDto signal, Integer quantity) {
        // Python StockBuyOrderRequest 모델에 맞는 데이터 구조 (인증 정보 제외)
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("dmst_stex_tp", "KRX");                         // 국내거래소구분
        requestBody.put("stk_cd", signal.getSymbol());                  // 종목코드
        requestBody.put("ord_qty", quantity.toString());                // 주문수량
        requestBody.put("ord_uv", signal.getCurrentPrice().toString()); // 주문단가 (Python API 필드명)
        requestBody.put("trde_tp", "0");                               // 매매구분 (0: 보통지정가)
        requestBody.put("cond_uv", "");                                // 조건단가 (빈값)
        requestBody.put("dry_run", signal.getDryRun());                // 모의/실전 모드 정보
        
        // 전략 메타데이터 (추가 정보 - Python에서 무시될 수 있음)
        requestBody.put("strategy_name", signal.getStrategyName());
        requestBody.put("signal_confidence", signal.getConfidence().toString());
        requestBody.put("signal_reason", signal.getReason());
        
        if (signal.getTargetPrice() != null) {
            requestBody.put("target_price", signal.getTargetPrice().toString());
        }
        
        if (signal.getStopLoss() != null) {
            requestBody.put("stop_loss", signal.getStopLoss().toString());
        }
        
        log.debug("키움 매수 주문 요청 생성 완료 (헤더 기반 인증): {}", signal.getSymbol());
        return requestBody;
    }
    
    /**
     * 키움 매도 주문 요청 생성 (Python API StockSellOrderRequest 스펙) - 헤더 기반
     * 
     * @param signal 매매신호
     * @param quantity 수량
     * @return 주문 요청 데이터 (Python API 형식, 인증 정보는 헤더로 전달)
     */
    private Map<String, Object> createSellOrderRequest(TradingSignalDto signal, Integer quantity) {
        // Python StockSellOrderRequest 모델에 맞는 데이터 구조 (인증 정보 제외)
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("dmst_stex_tp", "KRX");                         // 국내거래소구분
        requestBody.put("stk_cd", signal.getSymbol());                  // 종목코드
        requestBody.put("ord_qty", quantity.toString());                // 주문수량
        requestBody.put("ord_uv", signal.getCurrentPrice().toString()); // 주문단가 (Python API 필드명)
        requestBody.put("trde_tp", "0");                               // 매매구분 (0: 보통지정가)
        requestBody.put("cond_uv", "");                                // 조건단가 (빈값)
        requestBody.put("dry_run", signal.getDryRun());                // 모의/실전 모드 정보
        
        // 전략 메타데이터 (추가 정보 - Python에서 무시될 수 있음)
        requestBody.put("strategy_name", signal.getStrategyName());
        requestBody.put("signal_confidence", signal.getConfidence().toString());
        requestBody.put("signal_reason", signal.getReason());
        
        if (signal.getTargetPrice() != null) {
            requestBody.put("target_price", signal.getTargetPrice().toString());
        }
        
        if (signal.getStopLoss() != null) {
            requestBody.put("stop_loss", signal.getStopLoss().toString());
        }
        
        log.debug("키움 매도 주문 요청 생성 완료 (헤더 기반 인증): {}", signal.getSymbol());
        return requestBody;
    }
    
    /**
     * 키움 어댑터로 주문 전송 (재시도 로직 포함)
     * 
     * @param orderRequest 주문 요청
     * @param orderType 주문 타입 ("buy" or "sell")
     * @param signal 매매신호 (토큰 획득용)
     * @return 키움 API 응답
     */
    private Map<String, Object> sendOrderToKiwoom(Map<String, Object> orderRequest, String orderType, TradingSignalDto signal) {
        // 키움 API 실제 엔드포인트 사용
        String url;
        if ("buy".equals(orderType)) {
            url = kiwoomAdapterUrl + "/api/fn_kt10000";  // 키움 주식 매수주문
        } else if ("sell".equals(orderType)) {
            url = kiwoomAdapterUrl + "/api/fn_kt10001";  // 키움 주식 매도주문
        } else {
            throw new IllegalArgumentException("지원하지 않는 주문 타입: " + orderType);
        }
        
        // Query Parameter 추가 (Python API 요구사항)
        String urlWithParams = url + "?cont_yn=N&next_key=";
        
        // 키움 인증 정보 조회
        KiwoomAuthInfo authInfo = getKiwoomAuthInfo(signal);
        
        Exception lastException = null;
        
        // 재시도 로직
        for (int attempt = 1; attempt <= retryAttempts; attempt++) {
            try {
                log.info("키움 주문 API 호출 시도 {}/{}: {}", attempt, retryAttempts, urlWithParams);
                
                Mono<Map<String, Object>> responseMono = kiwoomWebClient.post()
                        .uri(urlWithParams)
                        .headers(h -> {
                            h.setContentType(MediaType.APPLICATION_JSON);
                            h.set("User-Agent", "QuantumTradingPlatform/1.0");
                            h.set("Authorization", "Bearer " + authInfo.getAccessToken());
                            h.set("X-Kiwoom-Access-Token", authInfo.getAccessToken());
                            h.set("X-Kiwoom-App-Key", authInfo.getApiKey());
                            h.set("X-Kiwoom-App-Secret", authInfo.getApiSecret());
                            h.set("X-Kiwoom-Base-Url", authInfo.getBaseUrl());
                            h.set("X-Kiwoom-Mode", authInfo.isRealMode() ? "real" : "sandbox");
                        })
                        .bodyValue(orderRequest)
                        .retrieve()
                        .bodyToMono((Class<Map<String, Object>>) (Class<?>) Map.class);
                
                Map<String, Object> response = responseMono.block();
                
                if (response != null) {
                    log.info("키움 주문 API 호출 성공");
                    return response;
                } else {
                    throw new RuntimeException("키움 API 응답이 null입니다");
                }
                
            } catch (WebClientException e) {
                lastException = e;
                log.warn("키움 어댑터 연결 실패 - 재시도 {}/{}: {}", attempt, retryAttempts, e.getMessage());
                
                if (attempt < retryAttempts) {
                    try {
                        Thread.sleep(1000 * attempt);  // 1초, 2초, 3초 대기
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException("주문 처리 중단됨", ie);
                    }
                }
                
            } catch (Exception e) {
                lastException = e;
                log.error("키움 주문 API 호출 실패 - 재시도 {}/{}: {}", attempt, retryAttempts, e.getMessage());
                
                if (attempt < retryAttempts) {
                    try {
                        Thread.sleep(500 * attempt);  // 0.5초, 1초, 1.5초 대기
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException("주문 처리 중단됨", ie);
                    }
                }
            }
        }
        
        // 모든 재시도 실패
        throw new RuntimeException("키움 주문 API 호출 최종 실패: " + 
            (lastException != null ? lastException.getMessage() : "알 수 없는 오류"));
    }
    
    /**
     * 키움 API 응답 파싱
     * 
     * @param signal 원본 신호
     * @param quantity 주문 수량
     * @param response 키움 응답
     * @param orderType 주문 타입
     * @return 실행 결과
     */
    private OrderExecutionResultDto parseKiwoomResponse(
            TradingSignalDto signal, 
            Integer quantity, 
            Map<String, Object> response,
            String orderType) {
        
        try {
            // 키움 응답 구조: {"Code": 200, "Body": {...}}
            Object codeObj = response.get("Code");
            Object bodyObj = response.get("Body");
            
            if (codeObj == null) {
                return OrderExecutionResultDto.failure(signal, 
                    "키움 응답 형식 오류: Code 필드 없음", "INVALID_RESPONSE");
            }
            
            Integer code = Integer.valueOf(codeObj.toString());
            Map<String, Object> body = bodyObj instanceof Map ? (Map<String, Object>) bodyObj : new HashMap<>();
            
            if (code == 200) {
                return parseSuccessfulResponse(signal, quantity, body, orderType);
            } else {
                return parseFailureResponse(signal, code, body);
            }
            
        } catch (Exception e) {
            log.error("키움 응답 파싱 실패: {}", e.getMessage(), e);
            return OrderExecutionResultDto.failure(signal, 
                "응답 파싱 실패: " + e.getMessage(), "RESPONSE_PARSE_ERROR");
        }
    }
    
    /**
     * 성공 응답 파싱
     * 
     * @param signal 원본 신호
     * @param quantity 수량
     * @param body 응답 본문
     * @param orderType 주문 타입
     * @return 성공 결과
     */
    private OrderExecutionResultDto parseSuccessfulResponse(
            TradingSignalDto signal, 
            Integer quantity, 
            Map<String, Object> body, 
            String orderType) {
        
        String orderNo = getStringValue(body, "order_no");
        String message = getStringValue(body, "message", "주문 접수 완료");
        
        // 실행 가격 (체결가가 있으면 사용, 없으면 주문가 사용)
        BigDecimal executedPrice = signal.getCurrentPrice();
        Object executedPriceObj = body.get("executed_price");
        if (executedPriceObj != null) {
            try {
                executedPrice = new BigDecimal(executedPriceObj.toString());
            } catch (NumberFormatException e) {
                log.warn("실행 가격 파싱 실패, 주문가 사용: {}", executedPriceObj);
            }
        }
        
        // 거래 금액 계산
        BigDecimal totalAmount = executedPrice.multiply(BigDecimal.valueOf(quantity));
        
        // 수수료 및 세금 계산 (예시)
        BigDecimal commission = totalAmount.multiply(BigDecimal.valueOf(0.00015));  // 0.015%
        BigDecimal tax = BigDecimal.ZERO;
        if ("SELL".equals(orderType)) {
            tax = totalAmount.multiply(BigDecimal.valueOf(0.0025));  // 매도세 0.25%
        }
        
        OrderExecutionResultDto result = OrderExecutionResultDto.builder()
                .status(OrderExecutionResultDto.ExecutionStatus.SUCCESS)
                .message(message)
                .originalSignal(signal)
                .orderId("ORD_" + System.currentTimeMillis())
                .kiwoomOrderNumber(orderNo)
                .executedQuantity(quantity)
                .executedPrice(executedPrice)
                .totalAmount(totalAmount)
                .commission(commission)
                .tax(tax)
                .executedAt(LocalDateTime.now())
                .dryRun(false)
                .balanceUpdated(true)
                .portfolioUpdated(true)
                .build();
        
        // 순 거래금액 계산
        result.calculateNetAmount();
        
        log.info("키움 주문 성공: {} - 주문번호: {}, 체결가: {}, 총금액: {}", 
                signal.getSymbol(), orderNo, executedPrice, totalAmount);
        
        return result;
    }
    
    /**
     * 실패 응답 파싱
     * 
     * @param signal 원본 신호
     * @param code 오류 코드
     * @param body 응답 본문
     * @return 실패 결과
     */
    private OrderExecutionResultDto parseFailureResponse(
            TradingSignalDto signal, 
            Integer code, 
            Map<String, Object> body) {
        
        String errorMessage = getStringValue(body, "message", "알 수 없는 키움 API 오류");
        String errorCode = "KIWOOM_ERROR_" + code;
        
        log.warn("키움 주문 실패: {} - 코드: {}, 메시지: {}", signal.getSymbol(), code, errorMessage);
        
        return OrderExecutionResultDto.failure(signal, errorMessage, errorCode);
    }
    
    /**
     * Map에서 문자열 값 안전하게 추출
     * 
     * @param map 맵
     * @param key 키
     * @param defaultValue 기본값
     * @return 문자열 값
     */
    private String getStringValue(Map<String, Object> map, String key, String defaultValue) {
        Object value = map.get(key);
        return value != null ? value.toString() : defaultValue;
    }
    
    /**
     * Map에서 문자열 값 안전하게 추출 (기본값 null)
     * 
     * @param map 맵
     * @param key 키
     * @return 문자열 값
     */
    private String getStringValue(Map<String, Object> map, String key) {
        return getStringValue(map, key, null);
    }
    
    /**
     * 키움 어댑터 연결 상태 확인
     * 
     * @return 연결 가능하면 true
     */
    public boolean checkKiwoomConnection() {
        try {
            String healthUrl = kiwoomAdapterUrl + "/health";
            
            Mono<Map<String, Object>> responseMono = kiwoomWebClient.get()
                    .uri(healthUrl)
                    .retrieve()
                    .bodyToMono((Class<Map<String, Object>>) (Class<?>) Map.class);
                    
            Map<String, Object> response = responseMono.block();
            
            boolean isHealthy = (response != null);
            
            log.info("키움 어댑터 연결 상태: {}", isHealthy ? "정상" : "비정상");
            return isHealthy;
            
        } catch (Exception e) {
            log.warn("키움 어댑터 연결 확인 실패: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * 주문 취소 (향후 구현)
     * 
     * @param kiwoomOrderNo 키움 주문번호
     * @return 취소 결과
     */
    public boolean cancelOrder(String kiwoomOrderNo) {
        // TODO: 키움 주문 취소 API 구현
        log.info("주문 취소 요청: {}", kiwoomOrderNo);
        return false;
    }
    
    /**
     * 주문 상태 조회 (향후 구현)
     * 
     * @param kiwoomOrderNo 키움 주문번호
     * @return 주문 상태
     */
    public Map<String, Object> getOrderStatus(String kiwoomOrderNo) {
        // TODO: 키움 주문 상태 조회 API 구현
        log.info("주문 상태 조회: {}", kiwoomOrderNo);
        return new HashMap<>();
    }
    
    /**
     * 키움 액세스 토큰 획득
     * Python 어댑터의 fn_au10001을 호출하여 토큰을 가져옴
     * 
     * @return 키움 액세스 토큰
     */
    /**
     * 모드별 키움 액세스 토큰 획득 (자동매매용)
     * 
     * @param signal 매매신호 (모의/실전 모드 판단용)
     * @return 키움 액세스 토큰
     */
    private String getKiwoomAccessToken(TradingSignalDto signal) {
        try {
            boolean isRealMode = !signal.getDryRun(); // dryRun=false면 실전모드
            String userId = getCurrentUserId(); // 현재 사용자 ID 획득
            
            log.debug("Requesting {} mode Kiwoom access token for user: {}", 
                    isRealMode ? "real" : "mock", userId);

            // KiwoomTokenService를 통해 모드별 토큰 획득
            return kiwoomTokenService.getAccessToken(userId, isRealMode);
            
        } catch (Exception e) {
            log.error("키움 액세스 토큰 획득 중 예외 발생: {}", e.getMessage(), e);
            // Fallback: 기존 방식으로 토큰 획득 시도
            return getKiwoomAccessTokenFallback();
        }
    }

    /**
     * 현재 사용자 ID 획득 (Spring Security Context에서)
     */
    private String getCurrentUserId() {
        // TODO: Spring Security Context에서 현재 사용자 ID 추출
        // 현재는 하드코딩으로 처리 (실제 구현 시 수정 필요)
        return "current_user_id"; // Placeholder
    }

    /**
     * 기존 방식의 토큰 획득 (Fallback)
     */
    private String getKiwoomAccessTokenFallback() {
        try {
            // Python 어댑터의 토큰 발급 엔드포인트 호출
            String tokenUrl = kiwoomAdapterUrl + "/api/fn_au10001";
            
            Map<String, Object> tokenRequest = new HashMap<>();
            tokenRequest.put("data", new HashMap<>()); // 빈 데이터
            tokenRequest.put("cont_yn", "N");
            tokenRequest.put("next_key", "");
            
            Mono<Map<String, Object>> responseMono = kiwoomWebClient.post()
                    .uri(tokenUrl)
                    .header("Content-Type", "application/json")
                    .bodyValue(tokenRequest)
                    .retrieve()
                    .bodyToMono((Class<Map<String, Object>>) (Class<?>) Map.class);
                    
            Map<String, Object> response = responseMono.block();
            
            if (response != null) {
                Map<String, Object> responseBody = response;
                Object codeObj = responseBody.get("Code");
                Object bodyObj = responseBody.get("Body");
                
                if (codeObj != null && "200".equals(codeObj.toString()) && bodyObj instanceof Map) {
                    Map<String, Object> body = (Map<String, Object>) bodyObj;
                    Object tokenObj = body.get("token");
                    
                    if (tokenObj != null) {
                        log.debug("키움 액세스 토큰 획득 성공 (Fallback)");
                        return tokenObj.toString();
                    }
                }
            }
            
            log.warn("키움 액세스 토큰 획득 실패 - 기본값 사용");
            return "DEFAULT_TOKEN"; // Fallback
            
        } catch (Exception e) {
            log.error("키움 액세스 토큰 획득 중 오류: {}", e.getMessage(), e);
            return "DEFAULT_TOKEN"; // Fallback
        }
    }

    /**
     * 모드별 키움 인증 정보 조회
     * 
     * @param signal 매매신호 (모의/실전 모드 판단용)
     * @return 키움 인증 정보
     */
    private KiwoomAuthInfo getKiwoomAuthInfo(TradingSignalDto signal) {
        try {
            boolean isRealMode = !signal.getDryRun(); // dryRun=false면 실전모드
            String userId = getCurrentUserId(); // 현재 사용자 ID 획득
            
            log.debug("Requesting {} mode Kiwoom auth info for user: {}", 
                    isRealMode ? "real" : "mock", userId);

            // KiwoomTokenService를 통해 모드별 인증 정보 획득
            return kiwoomTokenService.getAuthInfo(userId, isRealMode);
            
        } catch (Exception e) {
            log.error("키움 인증 정보 획득 중 예외 발생: {}", e.getMessage(), e);
            
            // Fallback: 환경변수 기반 기본 인증 정보 생성
            return createFallbackAuthInfo(signal.getDryRun());
        }
    }

    /**
     * Fallback 인증 정보 생성 (환경변수 기반)
     * 
     * @param isDryRun 모의투자 모드 여부
     * @return 기본 인증 정보
     */
    private KiwoomAuthInfo createFallbackAuthInfo(Boolean isDryRun) {
        log.warn("Fallback 키움 인증 정보 사용 - 환경변수 기반");
        
        boolean isRealMode = !Boolean.TRUE.equals(isDryRun);
        
        // 기본값으로 인증 정보 생성 (실제 구현에서는 환경변수에서 읽어옴)
        return new KiwoomAuthInfo(
                "DEFAULT_TOKEN",           // accessToken
                "DEFAULT_API_KEY",         // apiKey
                "DEFAULT_API_SECRET",      // apiSecret
                isRealMode                 // realMode
        );
    }
}