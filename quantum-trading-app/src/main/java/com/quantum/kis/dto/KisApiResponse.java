package com.quantum.kis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * KIS API 공통 응답 래퍼
 * @param <T> 실제 데이터 타입
 */
public record KisApiResponse<T>(
        @JsonProperty("rt_cd")
        String rtCd,

        @JsonProperty("msg_cd")
        String msgCd,

        @JsonProperty("msg1")
        String msg1,

        @JsonProperty("output")
        T output
) {
    /**
     * API 호출 성공 여부를 확인한다.
     * @return 성공 시 true, 실패 시 false
     */
    public boolean isOK() {
        return "0".equals(rtCd);
    }

    /**
     * 오류 메시지를 반환한다.
     * @return 오류 메시지
     */
    public String getErrorMessage() {
        return msg1;
    }
}