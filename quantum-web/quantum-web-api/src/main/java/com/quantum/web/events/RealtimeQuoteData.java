package com.quantum.web.events;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 실시간 주식 시세 데이터 모델
 * 키움증권 WebSocket에서 수신한 실시간 시세를 처리하기 위한 구조화된 모델
 */
public class RealtimeQuoteData {

    // 기본 정보
    @JsonProperty("symbol")
    private String symbol;

    @JsonProperty("symbol_name")
    private String symbolName;

    @JsonProperty("data_type")
    private String dataType; // 0A, 0B, 0C 등

    @JsonProperty("timestamp")
    private LocalDateTime timestamp;

    // 시세 정보
    @JsonProperty("current_price")
    private BigDecimal currentPrice;

    @JsonProperty("change_amount")
    private BigDecimal changeAmount;

    @JsonProperty("change_rate")
    private BigDecimal changeRate;

    @JsonProperty("volume")
    private Long volume;

    @JsonProperty("trading_value")
    private BigDecimal tradingValue;

    // 호가 정보
    @JsonProperty("bid_price")
    private BigDecimal bidPrice;

    @JsonProperty("ask_price")
    private BigDecimal askPrice;

    @JsonProperty("bid_volume")
    private Long bidVolume;

    @JsonProperty("ask_volume")
    private Long askVolume;

    // 거래 정보
    @JsonProperty("high_price")
    private BigDecimal highPrice;

    @JsonProperty("low_price")
    private BigDecimal lowPrice;

    @JsonProperty("open_price")
    private BigDecimal openPrice;

    @JsonProperty("prev_close_price")
    private BigDecimal prevClosePrice;

    // 추가 정보
    @JsonProperty("market_cap")
    private BigDecimal marketCap;

    @JsonProperty("listed_shares")
    private Long listedShares;

    // Default constructor
    public RealtimeQuoteData() {}

    // Constructor with essential fields
    public RealtimeQuoteData(String symbol, String dataType, BigDecimal currentPrice, Long volume) {
        this.symbol = symbol;
        this.dataType = dataType;
        this.currentPrice = currentPrice;
        this.volume = volume;
        this.timestamp = LocalDateTime.now();
    }

    // Getters and Setters
    public String getSymbol() {
        return symbol;
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol;
    }

    public String getSymbolName() {
        return symbolName;
    }

    public void setSymbolName(String symbolName) {
        this.symbolName = symbolName;
    }

    public String getDataType() {
        return dataType;
    }

    public void setDataType(String dataType) {
        this.dataType = dataType;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    public BigDecimal getCurrentPrice() {
        return currentPrice;
    }

    public void setCurrentPrice(BigDecimal currentPrice) {
        this.currentPrice = currentPrice;
    }

    public BigDecimal getChangeAmount() {
        return changeAmount;
    }

    public void setChangeAmount(BigDecimal changeAmount) {
        this.changeAmount = changeAmount;
    }

    public BigDecimal getChangeRate() {
        return changeRate;
    }

    public void setChangeRate(BigDecimal changeRate) {
        this.changeRate = changeRate;
    }

    public Long getVolume() {
        return volume;
    }

    public void setVolume(Long volume) {
        this.volume = volume;
    }

    public BigDecimal getTradingValue() {
        return tradingValue;
    }

    public void setTradingValue(BigDecimal tradingValue) {
        this.tradingValue = tradingValue;
    }

    public BigDecimal getBidPrice() {
        return bidPrice;
    }

    public void setBidPrice(BigDecimal bidPrice) {
        this.bidPrice = bidPrice;
    }

    public BigDecimal getAskPrice() {
        return askPrice;
    }

    public void setAskPrice(BigDecimal askPrice) {
        this.askPrice = askPrice;
    }

    public Long getBidVolume() {
        return bidVolume;
    }

    public void setBidVolume(Long bidVolume) {
        this.bidVolume = bidVolume;
    }

    public Long getAskVolume() {
        return askVolume;
    }

    public void setAskVolume(Long askVolume) {
        this.askVolume = askVolume;
    }

    public BigDecimal getHighPrice() {
        return highPrice;
    }

    public void setHighPrice(BigDecimal highPrice) {
        this.highPrice = highPrice;
    }

    public BigDecimal getLowPrice() {
        return lowPrice;
    }

    public void setLowPrice(BigDecimal lowPrice) {
        this.lowPrice = lowPrice;
    }

    public BigDecimal getOpenPrice() {
        return openPrice;
    }

    public void setOpenPrice(BigDecimal openPrice) {
        this.openPrice = openPrice;
    }

    public BigDecimal getPrevClosePrice() {
        return prevClosePrice;
    }

    public void setPrevClosePrice(BigDecimal prevClosePrice) {
        this.prevClosePrice = prevClosePrice;
    }

    public BigDecimal getMarketCap() {
        return marketCap;
    }

    public void setMarketCap(BigDecimal marketCap) {
        this.marketCap = marketCap;
    }

    public Long getListedShares() {
        return listedShares;
    }

    public void setListedShares(Long listedShares) {
        this.listedShares = listedShares;
    }

    @Override
    public String toString() {
        return "RealtimeQuoteData{" +
                "symbol='" + symbol + '\'' +
                ", dataType='" + dataType + '\'' +
                ", currentPrice=" + currentPrice +
                ", changeAmount=" + changeAmount +
                ", changeRate=" + changeRate +
                ", volume=" + volume +
                ", timestamp=" + timestamp +
                '}';
    }
}