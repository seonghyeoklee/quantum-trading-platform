package com.quantum.api.kiwoom.dto.chart.common;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.experimental.SuperBuilder;

/**
 * 키움증권 차트 API 공통 응답 DTO
 * 모든 차트 API 응답의 기본 클래스
 */
@Data
@SuperBuilder
@Schema(description = "차트 API 공통 응답")
public abstract class BaseChartResponse {
    
    /**
     * 응답 코드 (키움 공통)
     */
    @JsonProperty("return_code")
    @Schema(description = "응답 코드", example = "0")
    private Integer returnCode;
    
    /**
     * 응답 메시지 (키움 공통)
     */
    @JsonProperty("return_msg")
    @Schema(description = "응답 메시지", example = "정상적으로 처리되었습니다")
    private String returnMsg;
    
    /**
     * 성공 여부 확인
     */
    public boolean isSuccess() {
        return returnCode != null && returnCode == 0;
    }
    
    /**
     * 오류 여부 확인
     */
    public boolean hasError() {
        return !isSuccess();
    }
    
    /**
     * 오류 메시지 반환
     */
    public String getErrorMessage() {
        if (isSuccess()) {
            return null;
        }
        return String.format("Error %d: %s", returnCode, returnMsg);
    }
    
    /**
     * 기본 생성자 (Jackson 역직렬화용)
     */
    protected BaseChartResponse() {}
}