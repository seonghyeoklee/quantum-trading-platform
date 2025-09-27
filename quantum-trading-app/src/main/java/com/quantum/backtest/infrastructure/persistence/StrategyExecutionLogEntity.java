package com.quantum.backtest.infrastructure.persistence;

import com.quantum.backtest.domain.strategy.StrategyCalculationLog;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 전략 계산 과정 로그 JPA 엔티티
 * strategy_execution_logs 테이블과 매핑
 */
@Entity
@Table(name = "strategy_execution_logs",
       indexes = {
           @Index(name = "idx_strategy_logs_backtest_id", columnList = "backtest_id"),
           @Index(name = "idx_strategy_logs_trade_day", columnList = "trade_day"),
           @Index(name = "idx_strategy_logs_log_type", columnList = "log_type")
       })
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StrategyExecutionLogEntity {

    private static final ObjectMapper objectMapper = new ObjectMapper();

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "backtest_id", nullable = false, length = 36)
    private String backtestId;

    @Column(name = "log_timestamp", nullable = false)
    private LocalDateTime logTimestamp;

    @Column(name = "trade_day", nullable = false)
    private LocalDate tradeDay;

    @Enumerated(EnumType.STRING)
    @Column(name = "log_type", nullable = false, length = 50)
    private StrategyCalculationLog.LogType logType;

    @Column(name = "strategy_type", nullable = false, length = 50)
    private String strategyType;

    @Column(name = "step_sequence", nullable = false)
    private Integer stepSequence;

    @Column(name = "description", length = 500)
    private String description;

    @Column(name = "input_data", columnDefinition = "TEXT")
    private String inputData;

    @Column(name = "calculation_details", columnDefinition = "TEXT")
    private String calculationDetails;

    @Column(name = "output_result", columnDefinition = "TEXT")
    private String outputResult;

    /**
     * 도메인 객체로부터 엔티티 생성
     */
    public static StrategyExecutionLogEntity from(StrategyCalculationLog log, String backtestId) {
        return StrategyExecutionLogEntity.builder()
                .backtestId(backtestId)
                .logTimestamp(log.timestamp())
                .tradeDay(log.tradeDay())
                .logType(log.logType())
                .strategyType(log.strategyType())
                .stepSequence(log.stepSequence())
                .description(log.description())
                .inputData(mapToJson(log.inputData()))
                .calculationDetails(mapToJson(log.calculationDetails()))
                .outputResult(mapToJson(log.outputResult()))
                .build();
    }

    /**
     * 엔티티를 도메인 객체로 변환
     */
    public StrategyCalculationLog toDomain() {
        Map<String, Object> inputDataMap = parseJsonToMap(inputData);
        Map<String, Object> calculationDetailsMap = parseJsonToMap(calculationDetails);
        Map<String, Object> outputResultMap = parseJsonToMap(outputResult);

        return new StrategyCalculationLog(
                logTimestamp,
                tradeDay,
                logType,
                strategyType,
                stepSequence != null ? stepSequence : 0,
                description,
                inputDataMap,
                calculationDetailsMap,
                outputResultMap
        );
    }

    /**
     * Map을 JSON 문자열로 변환
     */
    private static String mapToJson(Map<String, Object> map) {
        if (map == null || map.isEmpty()) {
            return "{}";
        }

        try {
            return objectMapper.writeValueAsString(map);
        } catch (JsonProcessingException e) {
            return "{}";
        }
    }

    /**
     * JSON 문자열을 Map으로 파싱
     */
    private Map<String, Object> parseJsonToMap(String json) {
        if (json == null || json.trim().isEmpty()) {
            return new HashMap<>();
        }

        try {
            return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        } catch (JsonProcessingException e) {
            return new HashMap<>();
        }
    }

    /**
     * Thymeleaf 템플릿에서 사용할 getter 메서드들 (JSON 문자열을 Map으로 변환)
     */
    public Map<String, Object> getInputDataMap() {
        return parseJsonToMap(this.inputData);
    }

    public Map<String, Object> getCalculationDetailsMap() {
        return parseJsonToMap(this.calculationDetails);
    }

    public Map<String, Object> getOutputResultMap() {
        return parseJsonToMap(this.outputResult);
    }
}