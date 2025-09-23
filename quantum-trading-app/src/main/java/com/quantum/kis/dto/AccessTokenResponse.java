package com.quantum.kis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * KIS OAuth 접근 토큰 응답
 */
public record AccessTokenResponse(
        @JsonProperty("access_token")
        String accessToken,

        @JsonProperty("access_token_token_expired")
        String accessTokenExpired,

        @JsonProperty("token_type")
        String tokenType,

        @JsonProperty("expires_in")
        Integer expiresIn
) {}