package com.quantum.web.service;

import com.influxdb.client.WriteApiBlocking;
import com.influxdb.client.QueryApi;
import com.influxdb.client.domain.WritePrecision;
import com.influxdb.client.write.Point;
import com.influxdb.query.FluxRecord;
import com.influxdb.query.FluxTable;
import com.quantum.web.config.InfluxDBConfig;
import com.quantum.web.events.RealtimeOrderData;
import com.quantum.web.events.RealtimeQuoteData;
import com.quantum.web.events.RealtimeScreenerData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * 시계열 데이터 저장 및 조회 서비스
 * InfluxDB를 사용하여 실시간 이벤트 데이터를 시계열로 저장
 */
@Service
public class TimeSeriesService {

    private static final Logger logger = LoggerFactory.getLogger(TimeSeriesService.class);

    private final WriteApiBlocking writeApi;
    private final QueryApi queryApi;
    private final InfluxDBConfig config;

    public TimeSeriesService(WriteApiBlocking writeApi, QueryApi queryApi, InfluxDBConfig config) {
        this.writeApi = writeApi;
        this.queryApi = queryApi;
        this.config = config;
    }

    /**
     * 주식 시세 데이터를 시계열 DB에 저장
     */
    @Async
    public CompletableFuture<Void> saveQuoteData(RealtimeQuoteData quoteData) {
        try {
            Point point = Point.measurement("stock_quotes")
                .time(Instant.now(), WritePrecision.MS)
                .addTag("symbol", quoteData.getSymbol())
                .addTag("data_type", quoteData.getDataType() != null ? quoteData.getDataType() : "unknown")
                .addField("current_price", quoteData.getCurrentPrice() != null ? quoteData.getCurrentPrice().doubleValue() : 0.0)
                .addField("volume", quoteData.getVolume() != null ? quoteData.getVolume() : 0L);

            // 선택적 필드들
            if (quoteData.getChangeAmount() != null) {
                point = point.addField("change_amount", quoteData.getChangeAmount().doubleValue());
            }
            if (quoteData.getChangeRate() != null) {
                point = point.addField("change_rate", quoteData.getChangeRate().doubleValue());
            }
            if (quoteData.getTradingValue() != null) {
                point = point.addField("trading_value", quoteData.getTradingValue().doubleValue());
            }

            // 호가 정보
            if (quoteData.getBidPrice() != null) {
                point = point.addField("bid_price", quoteData.getBidPrice().doubleValue());
            }
            if (quoteData.getAskPrice() != null) {
                point = point.addField("ask_price", quoteData.getAskPrice().doubleValue());
            }
            if (quoteData.getBidVolume() != null) {
                point = point.addField("bid_volume", quoteData.getBidVolume());
            }
            if (quoteData.getAskVolume() != null) {
                point = point.addField("ask_volume", quoteData.getAskVolume());
            }

            // OHLC 데이터
            if (quoteData.getHighPrice() != null) {
                point = point.addField("high_price", quoteData.getHighPrice().doubleValue());
            }
            if (quoteData.getLowPrice() != null) {
                point = point.addField("low_price", quoteData.getLowPrice().doubleValue());
            }
            if (quoteData.getOpenPrice() != null) {
                point = point.addField("open_price", quoteData.getOpenPrice().doubleValue());
            }
            if (quoteData.getPrevClosePrice() != null) {
                point = point.addField("prev_close_price", quoteData.getPrevClosePrice().doubleValue());
            }

            writeApi.writePoint(config.getBucket(), config.getOrg(), point);
            
            logger.debug("Successfully saved stock quote data to InfluxDB: symbol={}, price={}", 
                        quoteData.getSymbol(), quoteData.getCurrentPrice());

        } catch (Exception e) {
            logger.error("Failed to save stock quote data to InfluxDB: symbol={}", quoteData.getSymbol(), e);
        }

        return CompletableFuture.completedFuture(null);
    }

    /**
     * 주문 데이터를 시계열 DB에 저장
     */
    @Async
    public CompletableFuture<Void> saveOrderData(RealtimeOrderData orderData) {
        try {
            Point point = Point.measurement("order_events")
                .time(Instant.now(), WritePrecision.MS)
                .addTag("symbol", orderData.getSymbol())
                .addTag("account_number", orderData.getAccountNumber())
                .addTag("order_id", orderData.getOrderId())
                .addTag("order_type", orderData.getOrderType() != null ? orderData.getOrderType() : "unknown")
                .addTag("order_status", orderData.getOrderStatus() != null ? orderData.getOrderStatus() : "unknown")
                .addField("order_quantity", orderData.getOrderQuantity() != null ? orderData.getOrderQuantity() : 0)
                .addField("order_price", orderData.getOrderPrice() != null ? orderData.getOrderPrice().doubleValue() : 0.0);

            // 추가 필드들
            if (orderData.getExecutedQuantity() != null) {
                point = point.addField("executed_quantity", orderData.getExecutedQuantity());
            }
            if (orderData.getExecutedPrice() != null) {
                point = point.addField("executed_price", orderData.getExecutedPrice().doubleValue());
            }
            if (orderData.getRemainingQuantity() != null) {
                point = point.addField("remaining_quantity", orderData.getRemainingQuantity());
            }

            writeApi.writePoint(config.getBucket(), config.getOrg(), point);
            
            logger.debug("Successfully saved order data to InfluxDB: orderId={}, symbol={}, status={}", 
                        orderData.getOrderId(), orderData.getSymbol(), orderData.getOrderStatus());

        } catch (Exception e) {
            logger.error("Failed to save order data to InfluxDB: orderId={}", orderData.getOrderId(), e);
        }

        return CompletableFuture.completedFuture(null);
    }

    /**
     * 스크리너 데이터를 시계열 DB에 저장
     */
    @Async
    public CompletableFuture<Void> saveScreenerData(RealtimeScreenerData screenerData) {
        try {
            Point point = Point.measurement("screener_alerts")
                .time(Instant.now(), WritePrecision.MS)
                .addTag("condition_name", screenerData.getConditionName())
                .addTag("condition_index", screenerData.getConditionIndex() != null ? screenerData.getConditionIndex() : "unknown")
                .addTag("market_type", screenerData.getMarketType() != null ? screenerData.getMarketType() : "unknown")
                .addField("symbol_count", screenerData.getSymbols() != null ? screenerData.getSymbols().size() : 0);

            // 첫 10개 종목을 쉼표로 구분된 문자열로 저장
            if (screenerData.getSymbols() != null && !screenerData.getSymbols().isEmpty()) {
                String symbolList = screenerData.getSymbols().stream()
                    .limit(10)
                    .reduce((a, b) -> a + "," + b)
                    .orElse("");
                if (!symbolList.isEmpty()) {
                    point = point.addField("symbols_preview", symbolList);
                }
            }

            writeApi.writePoint(config.getBucket(), config.getOrg(), point);
            
            logger.debug("Successfully saved screener data to InfluxDB: condition={}, symbols={}", 
                        screenerData.getConditionName(), 
                        screenerData.getSymbols() != null ? screenerData.getSymbols().size() : 0);

        } catch (Exception e) {
            logger.error("Failed to save screener data to InfluxDB: condition={}", screenerData.getConditionName(), e);
        }

        return CompletableFuture.completedFuture(null);
    }

    /**
     * 특정 종목의 과거 시세 데이터 조회
     */
    public List<Map<String, Object>> getQuoteHistory(String symbol, String timeRange) {
        List<Map<String, Object>> results = new ArrayList<>();
        
        try {
            String query = String.format("""
                from(bucket: "%s")
                  |> range(start: -%s)
                  |> filter(fn: (r) => r._measurement == "stock_quotes" and r.symbol == "%s")
                  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                  |> sort(columns: ["_time"], desc: false)
                """, config.getBucket(), timeRange, symbol);

            List<FluxTable> tables = queryApi.query(query, config.getOrg());
            
            for (FluxTable table : tables) {
                for (FluxRecord record : table.getRecords()) {
                    Map<String, Object> point = new HashMap<>();
                    point.put("time", record.getTime());
                    point.put("symbol", record.getValueByKey("symbol"));
                    point.put("current_price", record.getValueByKey("current_price"));
                    point.put("volume", record.getValueByKey("volume"));
                    point.put("change_amount", record.getValueByKey("change_amount"));
                    point.put("change_rate", record.getValueByKey("change_rate"));
                    
                    results.add(point);
                }
            }

            logger.debug("Retrieved {} quote history records for symbol: {}", results.size(), symbol);
            
        } catch (Exception e) {
            logger.error("Failed to query quote history for symbol: {}", symbol, e);
        }
        
        return results;
    }

    /**
     * 특정 계좌의 과거 주문 데이터 조회
     */
    public List<Map<String, Object>> getOrderHistory(String accountNumber, String timeRange) {
        List<Map<String, Object>> results = new ArrayList<>();
        
        try {
            String query = String.format("""
                from(bucket: "%s")
                  |> range(start: -%s)
                  |> filter(fn: (r) => r._measurement == "order_events" and r.account_number == "%s")
                  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                  |> sort(columns: ["_time"], desc: false)
                """, config.getBucket(), timeRange, accountNumber);

            List<FluxTable> tables = queryApi.query(query, config.getOrg());
            
            for (FluxTable table : tables) {
                for (FluxRecord record : table.getRecords()) {
                    Map<String, Object> point = new HashMap<>();
                    point.put("time", record.getTime());
                    point.put("account_number", record.getValueByKey("account_number"));
                    point.put("order_id", record.getValueByKey("order_id"));
                    point.put("symbol", record.getValueByKey("symbol"));
                    point.put("order_type", record.getValueByKey("order_type"));
                    point.put("order_status", record.getValueByKey("order_status"));
                    point.put("order_quantity", record.getValueByKey("order_quantity"));
                    point.put("order_price", record.getValueByKey("order_price"));
                    point.put("executed_quantity", record.getValueByKey("executed_quantity"));
                    point.put("executed_price", record.getValueByKey("executed_price"));
                    
                    results.add(point);
                }
            }

            logger.debug("Retrieved {} order history records for account: {}", results.size(), accountNumber);
            
        } catch (Exception e) {
            logger.error("Failed to query order history for account: {}", accountNumber, e);
        }
        
        return results;
    }

    /**
     * 시계열 집계 데이터 조회 (분/시간/일별 평균, 최고가, 최저가 등)
     */
    public List<Map<String, Object>> getAggregatedData(String measurement, String symbol, 
                                                      String timeRange, String window, String aggregateFunction) {
        List<Map<String, Object>> results = new ArrayList<>();
        
        try {
            String query = String.format("""
                from(bucket: "%s")
                  |> range(start: -%s)
                  |> filter(fn: (r) => r._measurement == "%s" and r.symbol == "%s")
                  |> aggregateWindow(every: %s, fn: %s, createEmpty: false)
                  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                  |> sort(columns: ["_time"], desc: false)
                """, config.getBucket(), timeRange, measurement, symbol, window, aggregateFunction);

            List<FluxTable> tables = queryApi.query(query, config.getOrg());
            
            for (FluxTable table : tables) {
                for (FluxRecord record : table.getRecords()) {
                    Map<String, Object> point = new HashMap<>();
                    point.put("time", record.getTime());
                    point.put("symbol", record.getValueByKey("symbol"));
                    
                    // 모든 필드를 동적으로 추가
                    record.getValues().forEach((key, value) -> {
                        if (!key.startsWith("_") && !key.equals("result") && !key.equals("table")) {
                            point.put(key, value);
                        }
                    });
                    
                    results.add(point);
                }
            }

            logger.debug("Retrieved {} aggregated data records for symbol: {} with window: {}", 
                        results.size(), symbol, window);
            
        } catch (Exception e) {
            logger.error("Failed to query aggregated data for symbol: {} with window: {}", symbol, window, e);
        }
        
        return results;
    }
}