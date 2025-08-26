package com.quantum.web.events;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * 실시간 데이터 이벤트 (Kafka로부터 수신)
 * Python Kiwoom Adapter에서 발행하는 이벤트를 수신하기 위한 모델
 */
public class RealtimeDataEvent {

    @JsonProperty("event_type")
    private String eventType;

    @JsonProperty("event_id")
    private String eventId;

    @JsonProperty("timestamp")
    private LocalDateTime timestamp;

    @JsonProperty("source")
    private String source;

    @JsonProperty("symbol")
    private String symbol;

    @JsonProperty("data_type")
    private String dataType;

    @JsonProperty("data")
    private JsonNode data;

    @JsonProperty("metadata")
    private Map<String, Object> metadata;

    // Default constructor
    public RealtimeDataEvent() {}

    // Getters and Setters
    public String getEventType() {
        return eventType;
    }

    public void setEventType(String eventType) {
        this.eventType = eventType;
    }

    public String getEventId() {
        return eventId;
    }

    public void setEventId(String eventId) {
        this.eventId = eventId;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getSymbol() {
        return symbol;
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol;
    }

    public String getDataType() {
        return dataType;
    }

    public void setDataType(String dataType) {
        this.dataType = dataType;
    }

    public JsonNode getData() {
        return data;
    }

    public void setData(JsonNode data) {
        this.data = data;
    }

    public Map<String, Object> getMetadata() {
        return metadata;
    }

    public void setMetadata(Map<String, Object> metadata) {
        this.metadata = metadata;
    }

    @Override
    public String toString() {
        return "RealtimeDataEvent{" +
                "eventType='" + eventType + '\'' +
                ", eventId='" + eventId + '\'' +
                ", timestamp=" + timestamp +
                ", source='" + source + '\'' +
                ", symbol='" + symbol + '\'' +
                ", dataType='" + dataType + '\'' +
                ", metadata=" + metadata +
                '}';
    }
}