package com.quantum.web.service;

import com.quantum.web.dto.TradingSignalDto;
import com.quantum.web.dto.OrderExecutionResultDto;
import com.quantum.web.events.RealtimeDataEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * 자동매매 전략 실시간 모니터링 서비스
 * 
 * 실행 중인 전략들의 성과, 신호 처리 상태, 포트폴리오 변화 등을 
 * 실시간으로 추적하고 웹소켓을 통해 프론트엔드에 전송
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TradingStrategyMonitoringService {
    
    private final SimpMessagingTemplate messagingTemplate;
    private final ApplicationEventPublisher eventPublisher;
    private final RealtimeOrderTrackingService orderTrackingService;
    
    @Value("${trading.monitoring.enabled:true}")
    private boolean monitoringEnabled;
    
    @Value("${trading.monitoring.broadcast-interval:5000}")
    private long broadcastInterval;
    
    // 실시간 모니터링 데이터 저장소
    private final Map<String, StrategyMonitoringData> strategyMonitoringMap = new ConcurrentHashMap<>();
    private final Map<String, List<SignalProcessingEvent>> recentSignalEvents = new ConcurrentHashMap<>();
    private final Map<String, List<OrderExecutionEvent>> recentOrderEvents = new ConcurrentHashMap<>();
    
    // 통계 카운터
    private final AtomicLong totalSignalsProcessed = new AtomicLong(0);
    private final AtomicLong totalOrdersExecuted = new AtomicLong(0);
    private final AtomicLong totalSuccessfulOrders = new AtomicLong(0);
    private final AtomicLong totalRejectedSignals = new AtomicLong(0);
    
    @PostConstruct
    public void initialize() {
        if (monitoringEnabled) {
            log.info("🔍 Trading Strategy Monitoring Service started");
        } else {
            log.info("⏸️ Trading Strategy Monitoring Service is disabled");
        }
    }
    
    /**
     * 신호 처리 시작 기록
     */
    public void recordSignalProcessingStart(TradingSignalDto signal) {
        if (!monitoringEnabled) return;
        
        String strategyName = signal.getStrategyName();
        
        // 전략 모니터링 데이터 초기화 또는 업데이트
        strategyMonitoringMap.computeIfAbsent(strategyName, k -> 
            StrategyMonitoringData.builder()
                .strategyName(k)
                .status("ACTIVE")
                .startTime(LocalDateTime.now())
                .totalSignals(0)
                .successfulExecutions(0)
                .rejectedSignals(0)
                .totalProfitLoss(BigDecimal.ZERO)
                .build());
        
        // 신호 처리 이벤트 기록
        SignalProcessingEvent event = SignalProcessingEvent.builder()
            .eventId(UUID.randomUUID().toString())
            .strategyName(strategyName)
            .symbol(signal.getSymbol())
            .signalType(signal.getSignalType())
            .confidence(signal.getConfidence().doubleValue())
            .currentPrice(signal.getCurrentPrice())
            .quantity(signal.getQuantity())
            .status("PROCESSING")
            .timestamp(LocalDateTime.now())
            .reason("신호 처리 시작")
            .build();
        
        recentSignalEvents.computeIfAbsent(strategyName, k -> new ArrayList<>()).add(event);
        
        // 최근 이벤트만 유지 (최대 100개)
        List<SignalProcessingEvent> events = recentSignalEvents.get(strategyName);
        if (events.size() > 100) {
            events.removeAll(events.subList(0, events.size() - 100));
        }
        
        totalSignalsProcessed.incrementAndGet();
        strategyMonitoringMap.get(strategyName).incrementTotalSignals();
        
        log.info("📊 신호 처리 시작 기록: {} - {}", strategyName, signal.getSymbol());
    }
    
    /**
     * 신호 처리 완료 기록
     */
    public void recordSignalProcessingComplete(TradingSignalDto signal, OrderExecutionResultDto result) {
        if (!monitoringEnabled) return;
        
        String strategyName = signal.getStrategyName();
        StrategyMonitoringData monitoring = strategyMonitoringMap.get(strategyName);
        
        if (monitoring != null) {
            // 결과에 따른 통계 업데이트
            if (result.isSuccessful()) {
                monitoring.incrementSuccessfulExecutions();
                totalSuccessfulOrders.incrementAndGet();
                
                // P&L 계산 및 업데이트
                if (result.getNetAmount() != null) {
                    if ("SELL".equals(signal.getSignalType())) {
                        // 매도인 경우 수익/손실로 간주
                        monitoring.addProfitLoss(result.getNetAmount());
                    }
                }
            } else if (result.isRejected()) {
                monitoring.incrementRejectedSignals();
                totalRejectedSignals.incrementAndGet();
            }
            
            monitoring.setLastActivity(LocalDateTime.now());
        }
        
        // 주문 실행 이벤트 기록
        if (result.isSuccessful()) {
            OrderExecutionEvent orderEvent = OrderExecutionEvent.builder()
                .eventId(UUID.randomUUID().toString())
                .strategyName(strategyName)
                .symbol(signal.getSymbol())
                .orderType(signal.getSignalType())
                .quantity(result.getExecutedQuantity())
                .executedPrice(result.getExecutedPrice())
                .totalAmount(result.getTotalAmount())
                .commission(result.getCommission())
                .tax(result.getTax())
                .netAmount(result.getNetAmount())
                .kiwoomOrderId(result.getKiwoomOrderNumber())
                .status("EXECUTED")
                .timestamp(LocalDateTime.now())
                .dryRun(Boolean.TRUE.equals(result.getDryRun()))
                .build();
            
            recentOrderEvents.computeIfAbsent(strategyName, k -> new ArrayList<>()).add(orderEvent);
            
            // 최근 주문만 유지 (최대 50개)
            List<OrderExecutionEvent> orders = recentOrderEvents.get(strategyName);
            if (orders.size() > 50) {
                orders.removeAll(orders.subList(0, orders.size() - 50));
            }
            
            totalOrdersExecuted.incrementAndGet();
        }
        
        // 신호 이벤트 상태 업데이트
        List<SignalProcessingEvent> events = recentSignalEvents.get(strategyName);
        if (events != null && !events.isEmpty()) {
            SignalProcessingEvent lastEvent = events.get(events.size() - 1);
            lastEvent.setStatus(result.isSuccessful() ? "COMPLETED" : "FAILED");
            lastEvent.setReason(result.getMessage());
        }
        
        log.info("📊 신호 처리 완료 기록: {} - {} ({})", 
                strategyName, signal.getSymbol(), result.getStatus());
    }
    
    /**
     * 전략 시작 기록
     */
    public void recordStrategyStart(String strategyName, Map<String, Object> config) {
        if (!monitoringEnabled) return;
        
        StrategyMonitoringData monitoring = StrategyMonitoringData.builder()
            .strategyName(strategyName)
            .status("STARTING")
            .startTime(LocalDateTime.now())
            .lastActivity(LocalDateTime.now())
            .totalSignals(0)
            .successfulExecutions(0)
            .rejectedSignals(0)
            .totalProfitLoss(BigDecimal.ZERO)
            .configuration(config)
            .build();
        
        strategyMonitoringMap.put(strategyName, monitoring);
        
        log.info("🚀 전략 시작 기록: {}", strategyName);
        
        // 전략 시작 알림 전송
        broadcastStrategyUpdate(strategyName, "STARTED", "전략이 시작되었습니다");
    }
    
    /**
     * 전략 중지 기록
     */
    public void recordStrategyStop(String strategyName, String reason) {
        if (!monitoringEnabled) return;
        
        StrategyMonitoringData monitoring = strategyMonitoringMap.get(strategyName);
        if (monitoring != null) {
            monitoring.setStatus("STOPPED");
            monitoring.setStopTime(LocalDateTime.now());
            monitoring.setStopReason(reason);
            
            log.info("⏹️ 전략 중지 기록: {} - {}", strategyName, reason);
            
            // 전략 중지 알림 전송
            broadcastStrategyUpdate(strategyName, "STOPPED", reason);
        }
    }
    
    /**
     * 전략 성능 요약 조회
     */
    public StrategyPerformanceSummary getStrategyPerformance(String strategyName) {
        StrategyMonitoringData monitoring = strategyMonitoringMap.get(strategyName);
        if (monitoring == null) {
            return null;
        }
        
        List<SignalProcessingEvent> signals = recentSignalEvents.getOrDefault(strategyName, new ArrayList<>());
        List<OrderExecutionEvent> orders = recentOrderEvents.getOrDefault(strategyName, new ArrayList<>());
        
        // 성공률 계산
        double successRate = monitoring.getTotalSignals() > 0 ? 
            (double) monitoring.getSuccessfulExecutions() / monitoring.getTotalSignals() * 100.0 : 0.0;
        
        // 평균 수익률 계산
        double avgProfitRate = orders.isEmpty() ? 0.0 :
            orders.stream()
                .filter(o -> o.getNetAmount() != null && !Boolean.TRUE.equals(o.getDryRun()))
                .mapToDouble(o -> o.getNetAmount().doubleValue())
                .average()
                .orElse(0.0);
        
        return StrategyPerformanceSummary.builder()
            .strategyName(strategyName)
            .status(monitoring.getStatus())
            .runningTime(calculateRunningTime(monitoring))
            .totalSignals(monitoring.getTotalSignals())
            .successfulExecutions(monitoring.getSuccessfulExecutions())
            .rejectedSignals(monitoring.getRejectedSignals())
            .successRate(successRate)
            .totalProfitLoss(monitoring.getTotalProfitLoss())
            .averageProfitRate(avgProfitRate)
            .recentSignals(signals.stream().limit(10).collect(Collectors.toList()))
            .recentOrders(orders.stream().limit(10).collect(Collectors.toList()))
            .lastActivity(monitoring.getLastActivity())
            .build();
    }
    
    /**
     * 전체 시스템 상태 조회
     */
    public SystemMonitoringStatus getSystemStatus() {
        int activeStrategies = (int) strategyMonitoringMap.values().stream()
            .filter(m -> "ACTIVE".equals(m.getStatus()) || "STARTING".equals(m.getStatus()))
            .count();
        
        BigDecimal totalPnL = strategyMonitoringMap.values().stream()
            .map(StrategyMonitoringData::getTotalProfitLoss)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
        
        return SystemMonitoringStatus.builder()
            .activeStrategies(activeStrategies)
            .totalStrategies(strategyMonitoringMap.size())
            .totalSignalsProcessed(totalSignalsProcessed.get())
            .totalOrdersExecuted(totalOrdersExecuted.get())
            .totalSuccessfulOrders(totalSuccessfulOrders.get())
            .totalRejectedSignals(totalRejectedSignals.get())
            .overallSuccessRate(totalSignalsProcessed.get() > 0 ? 
                (double) totalSuccessfulOrders.get() / totalSignalsProcessed.get() * 100.0 : 0.0)
            .totalProfitLoss(totalPnL)
            .systemUptime(LocalDateTime.now())
            .build();
    }
    
    /**
     * 정기적으로 실시간 데이터를 브로드캐스트
     */
    @Scheduled(fixedDelayString = "${trading.monitoring.broadcast-interval:5000}")
    public void broadcastRealtimeUpdates() {
        if (!monitoringEnabled) return;
        
        try {
            // 시스템 전체 상태 브로드캐스트
            SystemMonitoringStatus systemStatus = getSystemStatus();
            messagingTemplate.convertAndSend("/topic/trading/system-status", systemStatus);
            
            // 각 전략별 성능 브로드캐스트
            strategyMonitoringMap.keySet().forEach(strategyName -> {
                StrategyPerformanceSummary performance = getStrategyPerformance(strategyName);
                messagingTemplate.convertAndSend(
                    "/topic/trading/strategy/" + strategyName, 
                    performance
                );
            });
            
        } catch (Exception e) {
            log.error("실시간 데이터 브로드캐스트 중 오류 발생: {}", e.getMessage(), e);
        }
    }
    
    /**
     * 전략 업데이트 브로드캐스트
     */
    private void broadcastStrategyUpdate(String strategyName, String eventType, String message) {
        try {
            Map<String, Object> update = new HashMap<>();
            update.put("strategyName", strategyName);
            update.put("eventType", eventType);
            update.put("message", message);
            update.put("timestamp", LocalDateTime.now());
            
            messagingTemplate.convertAndSend("/topic/trading/strategy-events", update);
        } catch (Exception e) {
            log.error("전략 업데이트 브로드캐스트 중 오류 발생: {}", e.getMessage(), e);
        }
    }
    
    /**
     * 실행 시간 계산
     */
    private long calculateRunningTime(StrategyMonitoringData monitoring) {
        LocalDateTime start = monitoring.getStartTime();
        LocalDateTime end = monitoring.getStopTime() != null ? 
            monitoring.getStopTime() : LocalDateTime.now();
        
        return java.time.Duration.between(start, end).getSeconds();
    }
    
    // === 내부 데이터 클래스들 ===
    
    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class StrategyMonitoringData {
        private String strategyName;
        private String status;
        private LocalDateTime startTime;
        private LocalDateTime stopTime;
        private LocalDateTime lastActivity;
        private String stopReason;
        private int totalSignals;
        private int successfulExecutions;
        private int rejectedSignals;
        private BigDecimal totalProfitLoss;
        private Map<String, Object> configuration;
        
        public void incrementTotalSignals() {
            this.totalSignals++;
        }
        
        public void incrementSuccessfulExecutions() {
            this.successfulExecutions++;
        }
        
        public void incrementRejectedSignals() {
            this.rejectedSignals++;
        }
        
        public void addProfitLoss(BigDecimal amount) {
            if (this.totalProfitLoss == null) {
                this.totalProfitLoss = BigDecimal.ZERO;
            }
            this.totalProfitLoss = this.totalProfitLoss.add(amount);
        }
    }
    
    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class SignalProcessingEvent {
        private String eventId;
        private String strategyName;
        private String symbol;
        private String signalType;
        private Double confidence;
        private BigDecimal currentPrice;
        private Integer quantity;
        private String status;
        private String reason;
        private LocalDateTime timestamp;
    }
    
    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class OrderExecutionEvent {
        private String eventId;
        private String strategyName;
        private String symbol;
        private String orderType;
        private Integer quantity;
        private BigDecimal executedPrice;
        private BigDecimal totalAmount;
        private BigDecimal commission;
        private BigDecimal tax;
        private BigDecimal netAmount;
        private String kiwoomOrderId;
        private String status;
        private LocalDateTime timestamp;
        private Boolean dryRun;
    }
    
    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class StrategyPerformanceSummary {
        private String strategyName;
        private String status;
        private long runningTime;
        private int totalSignals;
        private int successfulExecutions;
        private int rejectedSignals;
        private double successRate;
        private BigDecimal totalProfitLoss;
        private double averageProfitRate;
        private List<SignalProcessingEvent> recentSignals;
        private List<OrderExecutionEvent> recentOrders;
        private LocalDateTime lastActivity;
    }
    
    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class SystemMonitoringStatus {
        private int activeStrategies;
        private int totalStrategies;
        private long totalSignalsProcessed;
        private long totalOrdersExecuted;
        private long totalSuccessfulOrders;
        private long totalRejectedSignals;
        private double overallSuccessRate;
        private BigDecimal totalProfitLoss;
        private LocalDateTime systemUptime;
    }
}