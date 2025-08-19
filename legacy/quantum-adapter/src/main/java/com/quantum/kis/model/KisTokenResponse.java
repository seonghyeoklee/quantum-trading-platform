package com.quantum.kis.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/** KIS OAuth2 토큰 응답 Record 불변 객체로 토큰 정보를 안전하게 관리 */
public record KisTokenResponse(
        @JsonProperty("access_token") String accessToken,
        @JsonProperty("token_type") String tokenType,
        @JsonProperty("expires_in") Long expiresIn,
        @JsonProperty("access_token_token_expired") String accessTokenExpired) {}
