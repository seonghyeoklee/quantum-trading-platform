package com.quantum.web.service;

import com.quantum.web.dto.TradingSignalDto;
import com.quantum.web.dto.OrderExecutionResultDto;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.ResourceAccessException;

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
@RequiredArgsConstructor
public class KiwoomOrderService {
    
    private final RestTemplate restTemplate;
    
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
            Map<String, Object> response = sendOrderToKiwoom(orderRequest, "buy");
            
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
            Map<String, Object> response = sendOrderToKiwoom(orderRequest, "sell");
            
            return parseKiwoomResponse(signal, quantity, response, "SELL");
            
        } catch (Exception e) {
            log.error("매도 주문 실행 실패: {}", e.getMessage(), e);
            return OrderExecutionResultDto.failure(signal, 
                "매도 주문 실행 실패: " + e.getMessage(), 
                "SELL_ORDER_FAILED");
        }
    }
    
    /**
     * 키움 매수 주문 요청 생성
     * 
     * @param signal 매매신호
     * @param quantity 수량
     * @return 주문 요청 데이터
     */
    private Map<String, Object> createBuyOrderRequest(TradingSignalDto signal, Integer quantity) {
        Map<String, Object> request = new HashMap<>();
        
        // 기본 주문 정보
        request.put("stk_cd", signal.getSymbol());                    // 종목코드
        request.put("ord_qty", quantity.toString());                  // 주문수량
        request.put("ord_prc", signal.getCurrentPrice().toString());  // 주문가격
        request.put("sll_by_tp", "01");                              // 매매구분 (01: 매수)
        request.put("ord_tp", "01");                                 // 주문유형 (01: 지정가)
        
        // 전략 메타데이터
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("strategy_name", signal.getStrategyName());
        metadata.put("signal_confidence", signal.getConfidence().doubleValue());
        metadata.put("signal_reason", signal.getReason());
        metadata.put("signal_timestamp", signal.getTimestamp().toString());
        metadata.put("order_type", "BUY");
        
        if (signal.getTargetPrice() != null) {
            metadata.put("target_price", signal.getTargetPrice().toString());
        }
        
        if (signal.getStopLoss() != null) {
            metadata.put("stop_loss", signal.getStopLoss().toString());
        }
        
        request.put("metadata", metadata);
        
        log.debug("매수 주문 요청 생성 완료: {}", request);
        return request;
    }
    
    /**
     * 키움 매도 주문 요청 생성
     * 
     * @param signal 매매신호
     * @param quantity 수량
     * @return 주문 요청 데이터
     */
    private Map<String, Object> createSellOrderRequest(TradingSignalDto signal, Integer quantity) {
        Map<String, Object> request = new HashMap<>();
        
        // 기본 주문 정보
        request.put("stk_cd", signal.getSymbol());                    // 종목코드
        request.put("ord_qty", quantity.toString());                  // 주문수량
        request.put("ord_prc", signal.getCurrentPrice().toString());  // 주문가격
        request.put("sll_by_tp", "02");                              // 매매구분 (02: 매도)
        request.put("ord_tp", "01");                                 // 주문유형 (01: 지정가)
        
        // 전략 메타데이터
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("strategy_name", signal.getStrategyName());
        metadata.put("signal_confidence", signal.getConfidence().doubleValue());
        metadata.put("signal_reason", signal.getReason());
        metadata.put("signal_timestamp", signal.getTimestamp().toString());
        metadata.put("order_type", "SELL");
        
        if (signal.getTargetPrice() != null) {
            metadata.put("target_price", signal.getTargetPrice().toString());
        }
        
        if (signal.getStopLoss() != null) {
            metadata.put("stop_loss", signal.getStopLoss().toString());
        }
        
        request.put("metadata", metadata);
        
        log.debug("매도 주문 요청 생성 완료: {}", request);
        return request;
    }
    
    /**
     * 키움 어댑터로 주문 전송 (재시도 로직 포함)
     * 
     * @param orderRequest 주문 요청
     * @param orderType 주문 타입 ("buy" or "sell")
     * @return 키움 API 응답
     */
    private Map<String, Object> sendOrderToKiwoom(Map<String, Object> orderRequest, String orderType) {
        String url = kiwoomAdapterUrl + "/api/order/" + orderType;
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("User-Agent", "QuantumTradingPlatform/1.0");
        
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(orderRequest, headers);
        
        Exception lastException = null;
        
        // 재시도 로직
        for (int attempt = 1; attempt <= retryAttempts; attempt++) {
            try {
                log.info("키움 주문 API 호출 시도 {}/{}: {}", attempt, retryAttempts, url);
                
                ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
                
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    log.info("키움 주문 API 호출 성공: HTTP {}", response.getStatusCode());
                    return response.getBody();
                } else {
                    throw new RuntimeException("키움 API 응답 오류: HTTP " + response.getStatusCode());
                }
                
            } catch (ResourceAccessException e) {
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
            ResponseEntity<Map> response = restTemplate.getForEntity(healthUrl, Map.class);
            
            boolean isHealthy = response.getStatusCode().is2xxSuccessful() && 
                               response.getBody() != null;
            
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
}