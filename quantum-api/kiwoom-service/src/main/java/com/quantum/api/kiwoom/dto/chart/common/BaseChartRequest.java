package com.quantum.api.kiwoom.dto.chart.common;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;
import lombok.experimental.SuperBuilder;

/**
 * 키움증권 차트 API 공통 요청 DTO
 * 모든 차트 API의 기본 클래스
 */
@Data
@SuperBuilder
@Schema(description = "차트 API 공통 요청")
public abstract class BaseChartRequest {
    
    /**
     * API 타입 결정 (URL 라우팅용)
     */
    public abstract ChartApiType getApiType();
    
    /**
     * API ID 반환 (키움 api-id 헤더용)
     */
    public abstract String getApiId();
    
    /**
     * 수정주가구분 (모든 차트 API 공통)
     */
    @Schema(description = "수정주가구분", example = "1", allowableValues = {"0", "1"})
    @Builder.Default
    protected String updStkpcTp = "1"; // 기본값: 수정주가 적용
    
    /**
     * 요청 검증
     */
    public void validate() {
        if (updStkpcTp == null || (!updStkpcTp.equals("0") && !updStkpcTp.equals("1"))) {
            throw new IllegalArgumentException("수정주가구분은 0 또는 1이어야 합니다");
        }
    }
    
    /**
     * 기본 생성자 (Jackson 직렬화용)
     */
    protected BaseChartRequest() {}
}