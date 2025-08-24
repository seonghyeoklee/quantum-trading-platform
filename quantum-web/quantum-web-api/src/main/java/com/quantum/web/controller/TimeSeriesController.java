package com.quantum.web.controller;

import com.quantum.web.service.TimeSeriesService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 시계열 데이터 조회 REST API 컨트롤러
 * InfluxDB에 저장된 과거 시계열 데이터를 조회하는 API 제공
 */
@RestController
@RequestMapping("/api/v1/timeseries")
@CrossOrigin(origins = "*")
public class TimeSeriesController {

    private static final Logger logger = LoggerFactory.getLogger(TimeSeriesController.class);

    private final TimeSeriesService timeSeriesService;

    public TimeSeriesController(TimeSeriesService timeSeriesService) {
        this.timeSeriesService = timeSeriesService;
    }

    /**
     * 특정 종목의 시세 히스토리 조회
     * 
     * @param symbol 종목코드 (예: 005930)
     * @param timeRange 시간 범위 (예: 1h, 6h, 1d, 7d, 30d)
     * @return 시세 데이터 리스트
     */
    @GetMapping("/quotes/{symbol}")
    public ResponseEntity<Map<String, Object>> getQuoteHistory(
            @PathVariable String symbol,
            @RequestParam(defaultValue = "1d") String timeRange) {
        
        try {
            logger.info("Fetching quote history for symbol: {}, timeRange: {}", symbol, timeRange);
            
            List<Map<String, Object>> data = timeSeriesService.getQuoteHistory(symbol, timeRange);
            
            Map<String, Object> response = Map.of(
                "symbol", symbol,
                "timeRange", timeRange,
                "dataCount", data.size(),
                "data", data
            );
            
            logger.info("Successfully retrieved {} quote records for symbol: {}", data.size(), symbol);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Failed to fetch quote history for symbol: {}", symbol, e);
            Map<String, Object> errorResponse = Map.of(
                "error", "Failed to fetch quote history",
                "message", e.getMessage(),
                "symbol", symbol,
                "timeRange", timeRange
            );
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    /**
     * 특정 계좌의 주문 히스토리 조회
     * 
     * @param accountNumber 계좌번호
     * @param timeRange 시간 범위 (예: 1h, 6h, 1d, 7d, 30d)
     * @return 주문 데이터 리스트
     */
    @GetMapping("/orders/{accountNumber}")
    public ResponseEntity<Map<String, Object>> getOrderHistory(
            @PathVariable String accountNumber,
            @RequestParam(defaultValue = "1d") String timeRange) {
        
        try {
            logger.info("Fetching order history for account: {}, timeRange: {}", accountNumber, timeRange);
            
            List<Map<String, Object>> data = timeSeriesService.getOrderHistory(accountNumber, timeRange);
            
            Map<String, Object> response = Map.of(
                "accountNumber", accountNumber,
                "timeRange", timeRange,
                "dataCount", data.size(),
                "data", data
            );
            
            logger.info("Successfully retrieved {} order records for account: {}", data.size(), accountNumber);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Failed to fetch order history for account: {}", accountNumber, e);
            Map<String, Object> errorResponse = Map.of(
                "error", "Failed to fetch order history",
                "message", e.getMessage(),
                "accountNumber", accountNumber,
                "timeRange", timeRange
            );
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    /**
     * 시계열 집계 데이터 조회 (OHLC, 평균가 등)
     * 
     * @param measurement 측정 유형 (stock_quotes, order_events, screener_alerts)
     * @param symbol 종목코드
     * @param timeRange 시간 범위 (예: 1h, 6h, 1d, 7d, 30d)
     * @param window 집계 윈도우 (예: 1m, 5m, 15m, 1h, 1d)
     * @param aggregateFunction 집계 함수 (mean, max, min, first, last)
     * @return 집계된 시계열 데이터
     */
    @GetMapping("/aggregated/{measurement}/{symbol}")
    public ResponseEntity<Map<String, Object>> getAggregatedData(
            @PathVariable String measurement,
            @PathVariable String symbol,
            @RequestParam(defaultValue = "1d") String timeRange,
            @RequestParam(defaultValue = "1h") String window,
            @RequestParam(defaultValue = "mean") String aggregateFunction) {
        
        try {
            logger.info("Fetching aggregated data for measurement: {}, symbol: {}, timeRange: {}, window: {}, function: {}",
                       measurement, symbol, timeRange, window, aggregateFunction);
            
            // 지원되는 measurement 유형 검증
            if (!isValidMeasurement(measurement)) {
                Map<String, Object> errorResponse = Map.of(
                    "error", "Invalid measurement type",
                    "message", "Supported measurements: stock_quotes, order_events, screener_alerts",
                    "provided", measurement
                );
                return ResponseEntity.badRequest().body(errorResponse);
            }
            
            // 지원되는 집계 함수 검증
            if (!isValidAggregateFunction(aggregateFunction)) {
                Map<String, Object> errorResponse = Map.of(
                    "error", "Invalid aggregate function",
                    "message", "Supported functions: mean, max, min, first, last, sum, count",
                    "provided", aggregateFunction
                );
                return ResponseEntity.badRequest().body(errorResponse);
            }
            
            List<Map<String, Object>> data = timeSeriesService.getAggregatedData(
                measurement, symbol, timeRange, window, aggregateFunction);
            
            Map<String, Object> response = Map.of(
                "measurement", measurement,
                "symbol", symbol,
                "timeRange", timeRange,
                "window", window,
                "aggregateFunction", aggregateFunction,
                "dataCount", data.size(),
                "data", data
            );
            
            logger.info("Successfully retrieved {} aggregated records for {}/{}", 
                       data.size(), measurement, symbol);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Failed to fetch aggregated data for {}/{}", measurement, symbol, e);
            Map<String, Object> errorResponse = Map.of(
                "error", "Failed to fetch aggregated data",
                "message", e.getMessage(),
                "measurement", measurement,
                "symbol", symbol
            );
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    /**
     * 실시간 시세의 최근 데이터 조회 (최근 N개 레코드)
     * 
     * @param symbol 종목코드
     * @param limit 조회할 레코드 수 (기본값: 100)
     * @return 최근 시세 데이터
     */
    @GetMapping("/quotes/{symbol}/recent")
    public ResponseEntity<Map<String, Object>> getRecentQuotes(
            @PathVariable String symbol,
            @RequestParam(defaultValue = "100") int limit) {
        
        try {
            logger.info("Fetching recent {} quotes for symbol: {}", limit, symbol);
            
            // 시간 범위를 동적으로 계산 (limit에 따라)
            String timeRange = calculateTimeRangeFromLimit(limit);
            List<Map<String, Object>> data = timeSeriesService.getQuoteHistory(symbol, timeRange);
            
            // 최신순으로 정렬하고 limit만큼 반환
            data = data.stream()
                      .sorted((a, b) -> ((String) b.get("time")).compareTo((String) a.get("time")))
                      .limit(limit)
                      .toList();
            
            Map<String, Object> response = Map.of(
                "symbol", symbol,
                "limit", limit,
                "actualCount", data.size(),
                "data", data
            );
            
            logger.info("Successfully retrieved {} recent quotes for symbol: {}", data.size(), symbol);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Failed to fetch recent quotes for symbol: {}", symbol, e);
            Map<String, Object> errorResponse = Map.of(
                "error", "Failed to fetch recent quotes",
                "message", e.getMessage(),
                "symbol", symbol,
                "limit", limit
            );
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    /**
     * 시계열 데이터 통계 정보 조회
     * 
     * @param measurement 측정 유형
     * @param timeRange 시간 범위
     * @return 데이터 통계 정보
     */
    @GetMapping("/stats/{measurement}")
    public ResponseEntity<Map<String, Object>> getTimeSeriesStats(
            @PathVariable String measurement,
            @RequestParam(defaultValue = "1d") String timeRange) {
        
        try {
            logger.info("Fetching time series stats for measurement: {}, timeRange: {}", measurement, timeRange);
            
            if (!isValidMeasurement(measurement)) {
                Map<String, Object> errorResponse = Map.of(
                    "error", "Invalid measurement type",
                    "message", "Supported measurements: stock_quotes, order_events, screener_alerts",
                    "provided", measurement
                );
                return ResponseEntity.badRequest().body(errorResponse);
            }
            
            // 기본 통계 정보 (향후 확장 가능)
            Map<String, Object> stats = Map.of(
                "measurement", measurement,
                "timeRange", timeRange,
                "status", "available",
                "description", getDescriptionForMeasurement(measurement)
            );
            
            logger.info("Successfully retrieved stats for measurement: {}", measurement);
            return ResponseEntity.ok(stats);
            
        } catch (Exception e) {
            logger.error("Failed to fetch stats for measurement: {}", measurement, e);
            Map<String, Object> errorResponse = Map.of(
                "error", "Failed to fetch time series stats",
                "message", e.getMessage(),
                "measurement", measurement
            );
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    /**
     * 지원되는 measurement 유형 검증
     */
    private boolean isValidMeasurement(String measurement) {
        return measurement != null && (
            measurement.equals("stock_quotes") ||
            measurement.equals("order_events") ||
            measurement.equals("screener_alerts")
        );
    }

    /**
     * 지원되는 집계 함수 검증
     */
    private boolean isValidAggregateFunction(String function) {
        return function != null && (
            function.equals("mean") || function.equals("max") || function.equals("min") ||
            function.equals("first") || function.equals("last") || function.equals("sum") ||
            function.equals("count")
        );
    }

    /**
     * limit에 따른 적절한 시간 범위 계산
     */
    private String calculateTimeRangeFromLimit(int limit) {
        if (limit <= 100) return "1h";
        if (limit <= 500) return "6h";
        if (limit <= 1000) return "1d";
        if (limit <= 5000) return "7d";
        return "30d";
    }

    /**
     * measurement에 대한 설명 반환
     */
    private String getDescriptionForMeasurement(String measurement) {
        return switch (measurement) {
            case "stock_quotes" -> "실시간 주식 시세 데이터 (현재가, 거래량, 호가 등)";
            case "order_events" -> "주문 체결 이벤트 데이터 (주문 생성, 체결, 취소 등)";
            case "screener_alerts" -> "조건검색 알림 데이터 (조건 충족 종목 리스트)";
            default -> "알 수 없는 measurement 유형";
        };
    }
}