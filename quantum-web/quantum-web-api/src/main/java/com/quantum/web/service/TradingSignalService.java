package com.quantum.web.service;

import com.quantum.web.dto.OrderExecutionResultDto;
import com.quantum.web.dto.TradingSignalDto;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * 자동매매 전략 신호 처리 서비스
 * 
 * Python에서 받은 매매신호를 분석하여 실제 주문으로 처리하는 핵심 서비스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TradingSignalService {
    
    private final RestTemplate restTemplate;
    private final KiwoomOrderService kiwoomOrderService;
    
    @Value("${kiwoom.adapter.url:http://localhost:10201}")
    private String kiwoomAdapterUrl;
    
    @Value("${trading.signal.min-confidence:0.7}")
    private double minConfidence;
    
    @Value("${trading.signal.dry-run:true}")
    private boolean globalDryRun;
    
    @Value("${trading.signal.max-position-size:1000000}")
    private long maxPositionSize;  // 최대 포지션 크기 (원)
    
    // 인메모리 저장소 (실제 환경에서는 DB 사용)
    private final List<TradingSignalDto> recentSignals = new CopyOnWriteArrayList<>();
    private final Map<String, Boolean> strategyEnabledMap = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> strategyStatsMap = new ConcurrentHashMap<>();
    
    /**
     * 매매신호 처리 메인 로직
     * 
     * @param signalDto 처리할 매매신호
     * @return 처리 결과
     */
    public OrderExecutionResultDto processSignal(TradingSignalDto signalDto) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("매매신호 처리 시작: {}", signalDto.getSummary());
            
            // 1. 신호 유효성 검증
            ValidationResult validation = validateSignal(signalDto);
            if (!validation.isValid()) {
                log.warn("매매신호 검증 실패: {}", validation.getReason());
                return OrderExecutionResultDto.rejected(signalDto, validation.getReason());
            }
            
            // 2. 리스크 관리 체크
            RiskCheckResult riskCheck = checkRiskLimits(signalDto);
            if (!riskCheck.isAllowed()) {
                log.warn("리스크 체크 실패: {}", riskCheck.getReason());
                return OrderExecutionResultDto.rejected(signalDto, riskCheck.getReason());
            }
            
            // 3. 실행 수량 계산
            Integer executionQuantity = calculateExecutionQuantity(signalDto);
            if (executionQuantity <= 0) {
                return OrderExecutionResultDto.rejected(signalDto, "실행 가능한 수량이 없습니다");
            }
            
            // 4. 실제 주문 실행
            OrderExecutionResultDto result;
            boolean isDryRun = signalDto.getDryRun() || globalDryRun;
            
            if (isDryRun) {
                // 모의투자 처리
                result = processSignalDryRun(signalDto, executionQuantity);
                log.info("모의투자 처리 완료: {}", result.getSummary());
            } else {
                // 실제 주문 처리
                result = processSignalReal(signalDto, executionQuantity);
                log.info("실투자 처리 완료: {}", result.getSummary());
            }
            
            // 5. 처리 시간 기록
            long processingTime = System.currentTimeMillis() - startTime;
            result.setProcessingTimeMs(processingTime);
            
            // 6. 결과 저장 및 통계 업데이트
            saveSignalResult(signalDto, result);
            updateStrategyStats(signalDto, result);
            
            return result;
            
        } catch (Exception e) {
            log.error("매매신호 처리 중 예외 발생: {}", e.getMessage(), e);
            long processingTime = System.currentTimeMillis() - startTime;
            
            OrderExecutionResultDto result = OrderExecutionResultDto.failure(
                signalDto, 
                e.getMessage(), 
                "PROCESSING_ERROR"
            );
            result.setProcessingTimeMs(processingTime);
            
            return result;
        }
    }
    
    /**
     * 신호 유효성 검증
     * 
     * @param signal 검증할 신호
     * @return 검증 결과
     */
    private ValidationResult validateSignal(TradingSignalDto signal) {
        // 1. 전략 활성화 상태 확인
        if (!isStrategyEnabled(signal.getStrategyName())) {
            return ValidationResult.invalid("전략이 비활성화되어 있습니다");
        }
        
        // 2. 신호 유효기간 확인
        if (!signal.isValid()) {
            return ValidationResult.invalid("신호 유효기간이 만료되었습니다");
        }
        
        // 3. 신뢰도 확인
        if (!signal.isConfidenceAbove(minConfidence)) {
            return ValidationResult.invalid(
                String.format("신뢰도가 부족합니다 (%.2f < %.2f)", 
                    signal.getConfidence().doubleValue(), minConfidence));
        }
        
        // 4. 실행 가능한 신호 타입 확인
        if (!signal.isExecutable(minConfidence)) {
            return ValidationResult.invalid("실행 불가능한 신호입니다");
        }
        
        return ValidationResult.valid();
    }
    
    /**
     * 리스크 한도 체크
     * 
     * @param signal 체크할 신호
     * @return 리스크 체크 결과
     */
    private RiskCheckResult checkRiskLimits(TradingSignalDto signal) {
        // 1. 최대 포지션 크기 체크
        BigDecimal signalAmount = signal.getCurrentPrice().multiply(
            BigDecimal.valueOf(signal.getQuantity() != null ? signal.getQuantity() : 100));
        
        if (signalAmount.longValue() > maxPositionSize) {
            return RiskCheckResult.denied(
                String.format("포지션 크기 한도 초과 (%d > %d)", 
                    signalAmount.longValue(), maxPositionSize));
        }
        
        // 2. 시장 시간 확인 (실투자인 경우)
        if (!signal.getDryRun() && !isMarketHours()) {
            return RiskCheckResult.denied("장외 시간에는 실제 주문을 할 수 없습니다");
        }
        
        // 3. 중복 신호 체크 (같은 종목의 최근 신호)
        if (hasDuplicateRecentSignal(signal)) {
            return RiskCheckResult.denied("동일 종목에 대한 최근 신호가 이미 처리되었습니다");
        }
        
        return RiskCheckResult.allowed();
    }
    
    /**
     * 실행 수량 계산
     * 
     * @param signal 신호
     * @return 실행할 수량
     */
    private Integer calculateExecutionQuantity(TradingSignalDto signal) {
        if (signal.getQuantity() != null && signal.getQuantity() > 0) {
            return signal.getQuantity();
        }
        
        // 기본 수량 계산 로직
        BigDecimal availableAmount = BigDecimal.valueOf(maxPositionSize);
        if (signal.getQuantityRatio() != null) {
            availableAmount = availableAmount.multiply(signal.getQuantityRatio());
        } else {
            availableAmount = availableAmount.multiply(BigDecimal.valueOf(0.1));  // 기본 10%
        }
        
        return availableAmount.divide(signal.getCurrentPrice(), 0, BigDecimal.ROUND_DOWN).intValue();
    }
    
    /**
     * 모의투자 신호 처리
     * 
     * @param signal 처리할 신호
     * @param quantity 실행 수량
     * @return 처리 결과
     */
    private OrderExecutionResultDto processSignalDryRun(TradingSignalDto signal, Integer quantity) {
        // 가상의 체결 가격 (현재가 기준 ±0.1% 랜덤)
        BigDecimal executionPrice = signal.getCurrentPrice()
            .multiply(BigDecimal.valueOf(1.0 + (Math.random() - 0.5) * 0.002));
        
        // 가상 처리 시간 (50-200ms)
        try {
            Thread.sleep(50 + (long)(Math.random() * 150));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        
        OrderExecutionResultDto result = OrderExecutionResultDto.dryRun(signal, quantity, executionPrice);
        result.calculateNetAmount();
        
        return result;
    }
    
    /**
     * 실제 주문 처리
     * 
     * @param signal 처리할 신호
     * @param quantity 실행 수량
     * @return 처리 결과
     */
    private OrderExecutionResultDto processSignalReal(TradingSignalDto signal, Integer quantity) {
        try {
            log.info("실제 주문 처리 시작: {} {} {}주", signal.getSymbol(), signal.getSignalType(), quantity);
            
            // 키움 어댑터 연결 상태 확인
            if (!kiwoomOrderService.checkKiwoomConnection()) {
                return OrderExecutionResultDto.failure(signal, 
                    "키움 어댑터 연결 실패", "KIWOOM_CONNECTION_FAILED");
            }
            
            // KiwoomOrderService를 통한 실제 주문 실행
            return kiwoomOrderService.executeOrder(signal, quantity);
            
        } catch (Exception e) {
            log.error("실제 주문 처리 실패: {}", e.getMessage(), e);
            return OrderExecutionResultDto.failure(signal, 
                "실제 주문 처리 실패: " + e.getMessage(), "REAL_ORDER_PROCESSING_ERROR");
        }
    }
    
    /**
     * 키움 주문 요청 데이터 생성
     * 
     * @param signal 매매신호
     * @param quantity 수량
     * @return 주문 요청 데이터
     */
    private Map<String, Object> createKiwoomOrderRequest(TradingSignalDto signal, Integer quantity) {
        Map<String, Object> request = new HashMap<>();
        
        request.put("stk_cd", signal.getSymbol());  // 종목코드
        request.put("ord_qty", quantity.toString());  // 주문수량
        request.put("ord_prc", signal.getCurrentPrice().toString());  // 주문가격
        request.put("sll_by_tp", signal.getKiwoomOrderSide());  // 매매구분
        request.put("ord_tp", "01");  // 주문유형 (지정가)
        
        // 추가 주문 정보
        Map<String, String> metadata = new HashMap<>();
        metadata.put("strategy_name", signal.getStrategyName());
        metadata.put("signal_confidence", signal.getConfidence().toString());
        metadata.put("signal_reason", signal.getReason());
        
        request.put("metadata", metadata);
        
        return request;
    }
    
    /**
     * 키움 주문 응답 파싱
     * 
     * @param signal 원본 신호
     * @param quantity 주문 수량
     * @param response 키움 API 응답
     * @return 실행 결과
     */
    private OrderExecutionResultDto parseKiwoomOrderResponse(
            TradingSignalDto signal, 
            Integer quantity, 
            Map<String, Object> response) {
        
        // 키움 응답 예시: {"Code": 200, "Body": {"order_no": "12345", "message": "주문완료"}}
        Integer code = (Integer) response.get("Code");
        Map<String, Object> body = (Map<String, Object>) response.get("Body");
        
        if (code == 200 && body != null) {
            String orderNo = (String) body.get("order_no");
            
            return OrderExecutionResultDto.builder()
                    .status(OrderExecutionResultDto.ExecutionStatus.SUCCESS)
                    .message("키움증권 주문이 성공적으로 접수되었습니다")
                    .originalSignal(signal)
                    .orderId("ORDER_" + System.currentTimeMillis())
                    .kiwoomOrderNumber(orderNo)
                    .executedQuantity(quantity)
                    .executedPrice(signal.getCurrentPrice())
                    .totalAmount(signal.getCurrentPrice().multiply(BigDecimal.valueOf(quantity)))
                    .executedAt(LocalDateTime.now())
                    .dryRun(false)
                    .balanceUpdated(false)  // 체결 확인 후 업데이트
                    .portfolioUpdated(false)
                    .build();
        } else {
            String errorMsg = body != null ? (String) body.get("message") : "알 수 없는 오류";
            return OrderExecutionResultDto.failure(signal, errorMsg, "KIWOOM_ORDER_REJECTED");
        }
    }
    
    /**
     * 신호 처리 결과 저장
     * 
     * @param signal 원본 신호
     * @param result 처리 결과
     */
    private void saveSignalResult(TradingSignalDto signal, OrderExecutionResultDto result) {
        // 최근 신호 목록에 추가 (최대 1000개 유지)
        recentSignals.add(0, signal);  // 최신 것부터
        if (recentSignals.size() > 1000) {
            recentSignals.remove(recentSignals.size() - 1);
        }
        
        log.info("신호 처리 결과 저장: {} - {}", signal.getSummary(), result.getStatus());
    }
    
    /**
     * 전략 통계 업데이트
     * 
     * @param signal 처리된 신호
     * @param result 처리 결과
     */
    private void updateStrategyStats(TradingSignalDto signal, OrderExecutionResultDto result) {
        String strategyName = signal.getStrategyName();
        Map<String, Object> stats = strategyStatsMap.computeIfAbsent(strategyName, k -> new HashMap<>());
        
        // 기본 통계 초기화
        stats.putIfAbsent("total_signals", 0);
        stats.putIfAbsent("successful_executions", 0);
        stats.putIfAbsent("failed_executions", 0);
        stats.putIfAbsent("total_amount", BigDecimal.ZERO);
        stats.putIfAbsent("last_signal_time", LocalDateTime.now());
        
        // 통계 업데이트
        stats.put("total_signals", (Integer) stats.get("total_signals") + 1);
        stats.put("last_signal_time", LocalDateTime.now());
        
        if (result.isSuccessful()) {
            stats.put("successful_executions", (Integer) stats.get("successful_executions") + 1);
            if (result.getTotalAmount() != null) {
                BigDecimal currentTotal = (BigDecimal) stats.get("total_amount");
                stats.put("total_amount", currentTotal.add(result.getTotalAmount()));
            }
        } else {
            stats.put("failed_executions", (Integer) stats.get("failed_executions") + 1);
        }
        
        // 성공률 계산
        int total = (Integer) stats.get("total_signals");
        int successful = (Integer) stats.get("successful_executions");
        stats.put("success_rate", total > 0 ? (double) successful / total : 0.0);
    }
    
    // === 공개 메서드들 ===
    
    public List<TradingSignalDto> getRecentSignals(int limit) {
        return recentSignals.stream()
                .limit(limit)
                .toList();
    }
    
    public Map<String, Object> getStrategyStats(String strategyName) {
        return strategyStatsMap.getOrDefault(strategyName, new HashMap<>());
    }
    
    public void setStrategyEnabled(String strategyName, boolean enabled) {
        strategyEnabledMap.put(strategyName, enabled);
        log.info("전략 '{}' 활성화 상태 변경: {}", strategyName, enabled);
    }
    
    public void setExecutionMode(boolean dryRun) {
        this.globalDryRun = dryRun;
        log.warn("글로벌 실행 모드 변경: {}", dryRun ? "모의투자" : "실투자");
    }
    
    public Map<String, Object> getSystemStatus() {
        Map<String, Object> status = new HashMap<>();
        status.put("global_dry_run", globalDryRun);
        status.put("min_confidence", minConfidence);
        status.put("max_position_size", maxPositionSize);
        status.put("active_strategies", strategyEnabledMap.size());
        status.put("recent_signals_count", recentSignals.size());
        status.put("kiwoom_adapter_url", kiwoomAdapterUrl);
        status.put("market_hours", isMarketHours());
        status.put("system_time", LocalDateTime.now());
        return status;
    }
    
    // === 유틸리티 메서드들 ===
    
    private boolean isStrategyEnabled(String strategyName) {
        return strategyEnabledMap.getOrDefault(strategyName, true);  // 기본값: 활성화
    }
    
    private boolean isMarketHours() {
        LocalDateTime now = LocalDateTime.now();
        int hour = now.getHour();
        int dayOfWeek = now.getDayOfWeek().getValue();
        
        // 평일 9:00-15:30 (간단한 구현)
        return dayOfWeek <= 5 && hour >= 9 && hour < 16;
    }
    
    private boolean hasDuplicateRecentSignal(TradingSignalDto signal) {
        return recentSignals.stream()
                .filter(s -> s.getSymbol().equals(signal.getSymbol()))
                .filter(s -> s.getStrategyName().equals(signal.getStrategyName()))
                .anyMatch(s -> s.getTimestamp().isAfter(LocalDateTime.now().minusMinutes(5)));
    }
    
    // === 내부 클래스들 ===
    
    private static class ValidationResult {
        private final boolean valid;
        private final String reason;
        
        private ValidationResult(boolean valid, String reason) {
            this.valid = valid;
            this.reason = reason;
        }
        
        public static ValidationResult valid() {
            return new ValidationResult(true, null);
        }
        
        public static ValidationResult invalid(String reason) {
            return new ValidationResult(false, reason);
        }
        
        public boolean isValid() { return valid; }
        public String getReason() { return reason; }
    }
    
    private static class RiskCheckResult {
        private final boolean allowed;
        private final String reason;
        
        private RiskCheckResult(boolean allowed, String reason) {
            this.allowed = allowed;
            this.reason = reason;
        }
        
        public static RiskCheckResult allowed() {
            return new RiskCheckResult(true, null);
        }
        
        public static RiskCheckResult denied(String reason) {
            return new RiskCheckResult(false, reason);
        }
        
        public boolean isAllowed() { return allowed; }
        public String getReason() { return reason; }
    }
}