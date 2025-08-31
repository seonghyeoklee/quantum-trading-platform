package com.quantum.web.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import jakarta.validation.constraints.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 자동매매 설정 DTO
 *
 * 자동매매 설정 생성, 조회, 수정에 사용되는 데이터 전송 객체
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class AutoTradingConfigDto {

    /**
     * 자동매매 설정 생성 요청 DTO
     */
    @Builder
    public record CreateRequest(
            @NotBlank(message = "전략명은 필수입니다")
            @Size(max = 50, message = "전략명은 최대 50자까지 입력 가능합니다")
            String strategyName,

            @NotBlank(message = "종목 코드는 필수입니다")
            @Pattern(regexp = "^[A-Z0-9]{6}$", message = "종목 코드는 6자리 영숫자여야 합니다")
            String symbol,

            @NotNull(message = "투자 금액은 필수입니다")
            @DecimalMin(value = "100000", message = "최소 투자 금액은 100,000원입니다")
            @Digits(integer = 12, fraction = 2, message = "투자 금액 형식이 올바르지 않습니다")
            BigDecimal capital,

            @NotNull(message = "최대 포지션 크기는 필수입니다")
            @Min(value = 1, message = "최대 포지션 크기는 최소 1%입니다")
            @Max(value = 100, message = "최대 포지션 크기는 최대 100%입니다")
            Integer maxPositionSize,

            @NotNull(message = "손절 비율은 필수입니다")
            @DecimalMin(value = "0.1", message = "손절 비율은 최소 0.1%입니다")
            @DecimalMax(value = "50.0", message = "손절 비율은 최대 50%입니다")
            @Digits(integer = 2, fraction = 2, message = "손절 비율 형식이 올바르지 않습니다")
            BigDecimal stopLossPercent,

            @NotNull(message = "익절 비율은 필수입니다")
            @DecimalMin(value = "0.5", message = "익절 비율은 최소 0.5%입니다")
            @DecimalMax(value = "100.0", message = "익절 비율은 최대 100%입니다")
            @Digits(integer = 3, fraction = 2, message = "익절 비율 형식이 올바르지 않습니다")
            BigDecimal takeProfitPercent
    ) {}

    /**
     * 자동매매 설정 수정 요청 DTO
     */
    @Builder
    public record UpdateRequest(
            @Size(max = 50, message = "전략명은 최대 50자까지 입력 가능합니다")
            String strategyName,

            @DecimalMin(value = "100000", message = "최소 투자 금액은 100,000원입니다")
            @Digits(integer = 12, fraction = 2, message = "투자 금액 형식이 올바르지 않습니다")
            BigDecimal capital,

            @Min(value = 1, message = "최대 포지션 크기는 최소 1%입니다")
            @Max(value = 100, message = "최대 포지션 크기는 최대 100%입니다")
            Integer maxPositionSize,

            @DecimalMin(value = "0.1", message = "손절 비율은 최소 0.1%입니다")
            @DecimalMax(value = "50.0", message = "손절 비율은 최대 50%입니다")
            @Digits(integer = 2, fraction = 2, message = "손절 비율 형식이 올바르지 않습니다")
            BigDecimal stopLossPercent,

            @DecimalMin(value = "0.5", message = "익절 비율은 최소 0.5%입니다")
            @DecimalMax(value = "100.0", message = "익절 비율은 최대 100%입니다")
            @Digits(integer = 3, fraction = 2, message = "익절 비율 형식이 올바르지 않습니다")
            BigDecimal takeProfitPercent,

            Boolean isActive
    ) {}

    /**
     * 자동매매 설정 응답 DTO
     */
    @Builder
    public record Response(
            String id,
            String strategyName,
            String symbol,
            BigDecimal capital,
            Integer maxPositionSize,
            BigDecimal stopLossPercent,
            BigDecimal takeProfitPercent,
            Boolean isActive,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {}

    /**
     * 자동매매 설정 요약 DTO
     *
     * 목록 조회 시 사용되는 간소화된 정보
     */
    @Builder
    public record Summary(
            String id,
            String strategyName,
            String symbol,
            BigDecimal capital,
            String status, // running, paused, stopped
            BigDecimal totalReturn,
            Integer totalTrades,
            LocalDateTime createdAt
    ) {}
}