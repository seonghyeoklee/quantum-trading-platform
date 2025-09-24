package com.quantum.kis.infrastructure.adapter.in.web.dto;

/**
 * 토큰 발급 응답 DTO
 * @param token 발급된 토큰
 * @param tokenType 토큰 타입
 * @param environment KIS 환경
 * @param message 응답 메시지
 */
public record TokenIssueResponse(
        String token,
        String tokenType,
        String environment,
        String message
) {
}