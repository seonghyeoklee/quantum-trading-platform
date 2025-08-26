package com.quantum.web.events;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 실시간 스크리너 데이터 모델
 * 키움증권 조건검색에서 수신한 종목 데이터를 처리하기 위한 구조화된 모델
 */
public class RealtimeScreenerData {

    @JsonProperty("condition_name")
    private String conditionName;

    @JsonProperty("condition_index")
    private String conditionIndex;

    @JsonProperty("symbols")
    private List<String> symbols;

    @JsonProperty("timestamp")
    private LocalDateTime timestamp;

    @JsonProperty("market_type")
    private String marketType; // KOSPI, KOSDAQ

    // Default constructor
    public RealtimeScreenerData() {}

    // Constructor
    public RealtimeScreenerData(String conditionName, String conditionIndex, List<String> symbols) {
        this.conditionName = conditionName;
        this.conditionIndex = conditionIndex;
        this.symbols = symbols;
        this.timestamp = LocalDateTime.now();
    }

    // Getters and Setters
    public String getConditionName() {
        return conditionName;
    }

    public void setConditionName(String conditionName) {
        this.conditionName = conditionName;
    }

    public String getConditionIndex() {
        return conditionIndex;
    }

    public void setConditionIndex(String conditionIndex) {
        this.conditionIndex = conditionIndex;
    }

    public List<String> getSymbols() {
        return symbols;
    }

    public void setSymbols(List<String> symbols) {
        this.symbols = symbols;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    public String getMarketType() {
        return marketType;
    }

    public void setMarketType(String marketType) {
        this.marketType = marketType;
    }

    @Override
    public String toString() {
        return "RealtimeScreenerData{" +
                "conditionName='" + conditionName + '\'' +
                ", conditionIndex='" + conditionIndex + '\'' +
                ", symbols=" + symbols +
                ", timestamp=" + timestamp +
                ", marketType='" + marketType + '\'' +
                '}';
    }
}