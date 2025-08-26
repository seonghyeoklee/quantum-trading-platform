package com.quantum.web.events;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 실시간 주문 데이터 모델
 * 키움증권 주문 체결/잔고 실시간 데이터를 처리하기 위한 구조화된 모델
 */
public class RealtimeOrderData {

    @JsonProperty("order_id")
    private String orderId;

    @JsonProperty("account_number")
    private String accountNumber;

    @JsonProperty("symbol")
    private String symbol;

    @JsonProperty("symbol_name")
    private String symbolName;

    @JsonProperty("order_type")
    private String orderType; // 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정

    @JsonProperty("order_status")
    private String orderStatus; // 접수, 확인, 체결, 거부

    @JsonProperty("order_quantity")
    private Integer orderQuantity;

    @JsonProperty("order_price")
    private BigDecimal orderPrice;

    @JsonProperty("executed_quantity")
    private Integer executedQuantity;

    @JsonProperty("executed_price")
    private BigDecimal executedPrice;

    @JsonProperty("remaining_quantity")
    private Integer remainingQuantity;

    @JsonProperty("timestamp")
    private LocalDateTime timestamp;

    // Default constructor
    public RealtimeOrderData() {}

    // Constructor with essential fields
    public RealtimeOrderData(String orderId, String accountNumber, String symbol, String orderType, String orderStatus) {
        this.orderId = orderId;
        this.accountNumber = accountNumber;
        this.symbol = symbol;
        this.orderType = orderType;
        this.orderStatus = orderStatus;
        this.timestamp = LocalDateTime.now();
    }

    // Getters and Setters
    public String getOrderId() {
        return orderId;
    }

    public void setOrderId(String orderId) {
        this.orderId = orderId;
    }

    public String getAccountNumber() {
        return accountNumber;
    }

    public void setAccountNumber(String accountNumber) {
        this.accountNumber = accountNumber;
    }

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

    public String getOrderType() {
        return orderType;
    }

    public void setOrderType(String orderType) {
        this.orderType = orderType;
    }

    public String getOrderStatus() {
        return orderStatus;
    }

    public void setOrderStatus(String orderStatus) {
        this.orderStatus = orderStatus;
    }

    public Integer getOrderQuantity() {
        return orderQuantity;
    }

    public void setOrderQuantity(Integer orderQuantity) {
        this.orderQuantity = orderQuantity;
    }

    public BigDecimal getOrderPrice() {
        return orderPrice;
    }

    public void setOrderPrice(BigDecimal orderPrice) {
        this.orderPrice = orderPrice;
    }

    public Integer getExecutedQuantity() {
        return executedQuantity;
    }

    public void setExecutedQuantity(Integer executedQuantity) {
        this.executedQuantity = executedQuantity;
    }

    public BigDecimal getExecutedPrice() {
        return executedPrice;
    }

    public void setExecutedPrice(BigDecimal executedPrice) {
        this.executedPrice = executedPrice;
    }

    public Integer getRemainingQuantity() {
        return remainingQuantity;
    }

    public void setRemainingQuantity(Integer remainingQuantity) {
        this.remainingQuantity = remainingQuantity;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public String toString() {
        return "RealtimeOrderData{" +
                "orderId='" + orderId + '\'' +
                ", accountNumber='" + accountNumber + '\'' +
                ", symbol='" + symbol + '\'' +
                ", orderType='" + orderType + '\'' +
                ", orderStatus='" + orderStatus + '\'' +
                ", orderQuantity=" + orderQuantity +
                ", executedQuantity=" + executedQuantity +
                ", timestamp=" + timestamp +
                '}';
    }
}