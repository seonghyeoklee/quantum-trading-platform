package com.quantum.web.service;

import com.quantum.web.dto.TradingSignalDto;
import com.quantum.web.dto.OrderExecutionResultDto;
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
import java.util.concurrent.CompletableFuture;

/**
 * 키움증권 API 통합 서비스
 * 
 * Java 백엔드와 Python 키움 어댑터 간의 주문 처리를 담당하는 통합 서비스
 * - 매매신호를 키움 주문 API 형식으로 변환
 * - 비동기 주문 실행
 * - 응답 파싱 및 결과 처리
 * - Rate Limiting 및 재시도 로직
 */
@Slf4j
@Service
public class KiwoomApiIntegrationService {
    
    private final WebClient webClient;
    private final KiwoomTokenService kiwoomTokenService;
    
    public KiwoomApiIntegrationService(@Qualifier("kiwoomWebClient") WebClient webClient,
                                      KiwoomTokenService kiwoomTokenService) {
        this.webClient = webClient;
        this.kiwoomTokenService = kiwoomTokenService;
    }
    
    @Value("${kiwoom.adapter.url:http://localhost:10201}")
    private String kiwoomAdapterUrl;
    
    @Value("${kiwoom.api.timeout:30000}")
    private int apiTimeoutMs;
    
    @Value("${kiwoom.api.retry-attempts:3}")
    private int retryAttempts;
    
    @Value("${kiwoom.api.retry-delay:1000}")
    private int retryDelayMs;
    
    /**
     * 매매신호를 키움 주문으로 실행
     * 
     * @param signal 매매신호
     * @return 비동기 실행 결과
     */
    public CompletableFuture<OrderExecutionResultDto> executeTradeSignal(TradingSignalDto signal) {
        log.info("키움 API 주문 실행 시작: {} {} {}주", 
                signal.getSymbol(), 
                signal.getSignalType(), 
                signal.getQuantity());
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 신호 타입에 따른 주문 실행
                return switch (signal.getSignalType()) {
                    case "BUY" -> executeBuyOrder(signal);
                    case "SELL", "CLOSE" -> executeSellOrder(signal);
                    default -> OrderExecutionResultDto.rejected(signal, 
                        "지원하지 않는 신호 타입: " + signal.getSignalType());
                };
                
            } catch (Exception e) {
                log.error("키움 API 주문 실행 중 예외 발생: {}", e.getMessage(), e);
                return OrderExecutionResultDto.failure(signal, 
                    "주문 실행 중 오류: " + e.getMessage(), 
                    "EXECUTION_ERROR");
            }
        });
    }
    
    /**
     * 매수 주문 실행
     */
    private OrderExecutionResultDto executeBuyOrder(TradingSignalDto signal) {
        log.info("키움 매수 주문 실행: {}", signal.getSymbol());
        
        try {
            // 키움 매수 주문 요청 데이터 구성
            Map<String, Object> requestData = createBuyOrderRequest(signal);
            
            // 키움 fn_kt10000 API 호출
            Map<String, Object> response = callKiwoomApiWithRetry("/api/fn_kt10000", requestData, signal);
            
            // 응답 파싱 및 결과 생성
            return parseKiwoomOrderResponse(signal, response, "BUY");
            
        } catch (Exception e) {
            log.error("매수 주문 실행 실패: {}", e.getMessage(), e);
            return OrderExecutionResultDto.failure(signal, 
                "매수 주문 실패: " + e.getMessage(), 
                "BUY_ORDER_FAILED");
        }
    }
    
    /**
     * 매도 주문 실행
     */
    private OrderExecutionResultDto executeSellOrder(TradingSignalDto signal) {
        log.info("키움 매도 주문 실행: {}", signal.getSymbol());
        
        try {
            // 키움 매도 주문 요청 데이터 구성
            Map<String, Object> requestData = createSellOrderRequest(signal);
            
            // 키움 fn_kt10001 API 호출
            Map<String, Object> response = callKiwoomApiWithRetry("/api/fn_kt10001", requestData, signal);
            
            // 응답 파싱 및 결과 생성
            return parseKiwoomOrderResponse(signal, response, "SELL");
            
        } catch (Exception e) {
            log.error("매도 주문 실행 실패: {}", e.getMessage(), e);
            return OrderExecutionResultDto.failure(signal, 
                "매도 주문 실패: " + e.getMessage(), 
                "SELL_ORDER_FAILED");
        }
    }
    
    /**
     * 키움 매수 주문 요청 데이터 생성 (Python API StockBuyOrderRequest 스펙)
     */
    private Map<String, Object> createBuyOrderRequest(TradingSignalDto signal) {
        // Python StockBuyOrderRequest 모델에 맞는 데이터 구조 (Request Body)
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("dmst_stex_tp", "KRX");  // 국내거래소구분
        requestBody.put("stk_cd", signal.getSymbol());  // 종목코드
        requestBody.put("ord_qty", signal.getQuantity() != null ? 
            signal.getQuantity().toString() : "100");  // 주문수량
        requestBody.put("ord_uv", signal.getCurrentPrice().toString());  // 주문단가 (Python API 필드명)
        requestBody.put("trde_tp", "0");    // 매매유형 (0: 보통지정가)
        requestBody.put("cond_uv", "");     // 조건단가
        
        // 메타데이터 추가 (추가 정보 - Python에서 무시될 수 있음)
        requestBody.put("strategy_name", signal.getStrategyName());
        requestBody.put("signal_confidence", signal.getConfidence().toString());
        requestBody.put("signal_reason", signal.getReason());
        requestBody.put("signal_timestamp", signal.getTimestamp().toString());
        requestBody.put("dry_run", signal.getDryRun());
        
        return requestBody;
    }
    
    /**
     * 키움 매도 주문 요청 데이터 생성 (Python API StockSellOrderRequest 스펙)
     */
    private Map<String, Object> createSellOrderRequest(TradingSignalDto signal) {
        // Python StockSellOrderRequest 모델에 맞는 데이터 구조 (Request Body)
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("dmst_stex_tp", "KRX");  // 국내거래소구분
        requestBody.put("stk_cd", signal.getSymbol());  // 종목코드
        requestBody.put("ord_qty", signal.getQuantity() != null ? 
            signal.getQuantity().toString() : "100");  // 주문수량
        requestBody.put("ord_uv", signal.getCurrentPrice().toString());  // 주문단가 (Python API 필드명)
        requestBody.put("trde_tp", "0");    // 매매유형 (0: 보통지정가)
        requestBody.put("cond_uv", "");     // 조건단가
        
        // 메타데이터 추가 (추가 정보 - Python에서 무시될 수 있음)
        requestBody.put("strategy_name", signal.getStrategyName());
        requestBody.put("signal_confidence", signal.getConfidence().toString());
        requestBody.put("signal_reason", signal.getReason());
        requestBody.put("signal_timestamp", signal.getTimestamp().toString());
        requestBody.put("dry_run", signal.getDryRun());
        
        return requestBody;
    }
    
    /**
     * 재시도 로직이 포함된 키움 API 호출
     */
    private Map<String, Object> callKiwoomApiWithRetry(String endpoint, Map<String, Object> requestData, TradingSignalDto signal) {
        // Query Parameter 추가 (Python API 요구사항)
        String urlWithParams = kiwoomAdapterUrl + endpoint + "?cont_yn=N&next_key=";
        
        // HTTP Headers 설정 (Authorization 토큰 포함)
        String accessToken = getKiwoomAccessToken(signal); // 키움 인증 토큰
        
        Exception lastException = null;
        
        for (int attempt = 1; attempt <= retryAttempts; attempt++) {
            try {
                log.info("키움 API 호출 시도 {}/{}: {}", attempt, retryAttempts, urlWithParams);
                
                Mono<Map> responseMono = webClient.post()
                        .uri(urlWithParams)
                        .headers(h -> {
                            h.setContentType(MediaType.APPLICATION_JSON);
                            h.set("User-Agent", "QuantumTradingPlatform-OrderExecution/1.0");
                            h.set("Authorization", "Bearer " + accessToken);
                        })
                        .bodyValue(requestData)
                        .retrieve()
                        .bodyToMono(Map.class);
                
                Map response = responseMono.block();
                
                if (response != null) {
                    log.info("키움 API 호출 성공");
                    return response;
                } else {
                    throw new RuntimeException("키움 API 응답이 null입니다");
                }
                
            } catch (WebClientException e) {
                lastException = e;
                log.warn("키움 API 연결 실패 - 재시도 {}/{}: {}", attempt, retryAttempts, e.getMessage());
                
                if (attempt < retryAttempts) {
                    sleep(retryDelayMs * attempt);
                }
                
            } catch (Exception e) {
                lastException = e;
                log.error("키움 API 호출 실패 - 재시도 {}/{}: {}", attempt, retryAttempts, e.getMessage());
                
                if (attempt < retryAttempts) {
                    sleep(retryDelayMs);
                }
            }
        }
        
        throw new RuntimeException("키움 API 호출 최종 실패: " + 
            (lastException != null ? lastException.getMessage() : "알 수 없는 오류"));
    }
    
    /**
     * 키움 API 응답 파싱
     */
    private OrderExecutionResultDto parseKiwoomOrderResponse(
            TradingSignalDto signal, 
            Map<String, Object> response, 
            String orderType) {
        
        try {
            // 키움 API 응답 구조: {"Code": 200, "Body": {...}}
            Object codeObj = response.get("Code");
            Object bodyObj = response.get("Body");
            
            if (codeObj == null) {
                return OrderExecutionResultDto.failure(signal, 
                    "키움 API 응답 형식 오류: Code 필드 없음", "INVALID_RESPONSE");
            }
            
            Integer code = parseInteger(codeObj);
            Map<String, Object> body = bodyObj instanceof Map ? 
                (Map<String, Object>) bodyObj : new HashMap<>();
            
            if (code == 200) {
                return createSuccessResult(signal, body, orderType);
            } else {
                return createFailureResult(signal, code, body);
            }
            
        } catch (Exception e) {
            log.error("키움 API 응답 파싱 실패: {}", e.getMessage(), e);
            return OrderExecutionResultDto.failure(signal, 
                "응답 파싱 실패: " + e.getMessage(), "RESPONSE_PARSE_ERROR");
        }
    }
    
    /**
     * 성공 응답으로부터 결과 생성
     */
    private OrderExecutionResultDto createSuccessResult(
            TradingSignalDto signal, 
            Map<String, Object> body, 
            String orderType) {
        
        String orderNo = extractString(body, "ord_no");
        String message = extractString(body, "msg1", "주문이 접수되었습니다");
        
        // 실행 가격 (키움에서 체결 정보가 있으면 사용)
        BigDecimal executedPrice = signal.getCurrentPrice();
        Object priceObj = body.get("ord_uv");
        if (priceObj != null) {
            try {
                executedPrice = new BigDecimal(priceObj.toString());
            } catch (NumberFormatException e) {
                log.warn("실행 가격 파싱 실패, 주문가 사용: {}", priceObj);
            }
        }
        
        Integer quantity = signal.getQuantity() != null ? signal.getQuantity() : 100;
        BigDecimal totalAmount = executedPrice.multiply(BigDecimal.valueOf(quantity));
        
        // 수수료 및 세금 계산
        BigDecimal commission = calculateCommission(totalAmount);
        BigDecimal tax = "SELL".equals(orderType) ? calculateTax(totalAmount) : BigDecimal.ZERO;
        
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
                .dryRun(Boolean.TRUE.equals(signal.getDryRun()))
                .balanceUpdated(true)
                .portfolioUpdated(true)
                .build();
        
        // 순 거래금액 계산
        result.calculateNetAmount();
        
        log.info("키움 {} 주문 성공: {} - 주문번호: {}, 가격: {}, 총액: {}", 
                orderType, signal.getSymbol(), orderNo, executedPrice, totalAmount);
        
        return result;
    }
    
    /**
     * 실패 응답으로부터 결과 생성
     */
    private OrderExecutionResultDto createFailureResult(
            TradingSignalDto signal, 
            Integer code, 
            Map<String, Object> body) {
        
        String errorMessage = extractString(body, "msg1", "키움 API 오류");
        String errorCode = "KIWOOM_ERROR_" + code;
        
        log.warn("키움 주문 실패: {} - 코드: {}, 메시지: {}", 
                signal.getSymbol(), code, errorMessage);
        
        return OrderExecutionResultDto.failure(signal, errorMessage, errorCode);
    }
    
    /**
     * 수수료 계산 (0.015%)
     */
    private BigDecimal calculateCommission(BigDecimal amount) {
        return amount.multiply(BigDecimal.valueOf(0.00015));
    }
    
    /**
     * 매도세 계산 (0.25%)
     */
    private BigDecimal calculateTax(BigDecimal amount) {
        return amount.multiply(BigDecimal.valueOf(0.0025));
    }
    
    /**
     * Object를 Integer로 안전하게 변환
     */
    private Integer parseInteger(Object obj) {
        if (obj == null) return null;
        if (obj instanceof Integer) return (Integer) obj;
        try {
            return Integer.valueOf(obj.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }
    
    /**
     * Map에서 문자열 값 안전하게 추출
     */
    private String extractString(Map<String, Object> map, String key, String defaultValue) {
        Object value = map.get(key);
        return value != null ? value.toString() : defaultValue;
    }
    
    private String extractString(Map<String, Object> map, String key) {
        return extractString(map, key, null);
    }
    
    /**
     * 안전한 스레드 대기
     */
    private void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("스레드 대기 중단됨", e);
        }
    }
    
    /**
     * 키움 어댑터 연결 상태 확인
     */
    public boolean checkAdapterHealth() {
        try {
            String healthUrl = kiwoomAdapterUrl + "/health";
            
            Mono<Map> responseMono = webClient.get()
                    .uri(healthUrl)
                    .retrieve()
                    .bodyToMono(Map.class);
                    
            Map response = responseMono.block();
            
            boolean isHealthy = (response != null);
            log.info("키움 어댑터 연결 상태: {}", isHealthy ? "정상" : "비정상");
            
            return isHealthy;
            
        } catch (Exception e) {
            log.warn("키움 어댑터 연결 확인 실패: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * 모드별 키움 액세스 토큰 조회
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
            log.error("키움 액세스 토큰 조회 실패: {}", e.getMessage(), e);
            return "fallback_token"; // Fallback
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
}