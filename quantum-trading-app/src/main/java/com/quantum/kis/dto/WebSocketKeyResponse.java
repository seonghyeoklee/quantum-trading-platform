package com.quantum.kis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * KIS 웹소켓 접속키 응답
 */
public record WebSocketKeyResponse(
        @JsonProperty("approval_key")
        String approvalKey
) {}