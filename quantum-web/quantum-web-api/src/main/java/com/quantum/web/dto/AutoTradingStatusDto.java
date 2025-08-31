package com.quantum.web.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * 자동매매 상태 DTO
 *
 * 자동매매 실행 상태 및 성과 정보를 전송하는 데이터 객체
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class AutoTradingStatusDto {

    /**
     * 자동매매 상태 응답 DTO
     */
    @Builder
    public record Response(
            String id,
            String configId,
            String status,      // created, running, paused, stopped, error
            Integer totalTrades,
            Integer winningTrades,
            BigDecimal totalProfit,
            BigDecimal totalReturn,
            BigDecimal maxDrawdown,
            LocalDateTime startedAt,
            LocalDateTime stoppedAt,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {
        /**
         * 승률 계산 (백분율)
         */
        public BigDecimal getWinRate() {
            if (totalTrades == null || totalTrades == 0) {
                return BigDecimal.ZERO;
            }
            
            return BigDecimal.valueOf(winningTrades)
                    .divide(BigDecimal.valueOf(totalTrades), 4, java.math.RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
        }

        /**
         * 평균 수익률 계산 (거래당)
         */
        public BigDecimal getAverageReturn() {
            if (totalTrades == null || totalTrades == 0 || totalReturn == null) {
                return BigDecimal.ZERO;
            }
            
            return totalReturn.divide(BigDecimal.valueOf(totalTrades), 4, java.math.RoundingMode.HALF_UP);
        }

        /**
         * 상태 한글명 반환
         */
        public String getStatusKorean() {
            return switch (status) {
                case "created" -> "생성됨";
                case "running" -> "실행중";
                case "paused" -> "일시정지";
                case "stopped" -> "정지됨";
                case "error" -> "오류";
                default -> "알 수 없음";
            };
        }
    }

    /**
     * 자동매매 상태 요약 DTO
     *
     * 대시보드에서 사용되는 간소화된 상태 정보
     */
    @Builder
    public record Summary(
            String configId,
            String strategyName,
            String symbol,
            String status,
            BigDecimal totalReturn,
            Integer totalTrades,
            BigDecimal winRate,
            LocalDateTime lastUpdated
    ) {}

    /**
     * 실시간 성과 정보 DTO
     *
     * WebSocket을 통해 전송되는 실시간 성과 데이터
     */
    @Builder
    public record RealtimePerformance(
            String configId,
            BigDecimal currentReturn,
            BigDecimal todayReturn,
            Integer todayTrades,
            BigDecimal currentDrawdown,
            BigDecimal unrealizedPnl,
            Map<String, Object> positions, // 현재 포지션 정보
            LocalDateTime timestamp
    ) {}

    /**
     * 자동매매 통계 DTO
     *
     * 상세 분석용 통계 정보
     */
    @Builder
    public record Statistics(
            String configId,
            
            // 기본 통계
            Integer totalTrades,
            Integer winningTrades,
            Integer losingTrades,
            BigDecimal winRate,
            
            // 수익/손실 통계  
            BigDecimal totalProfit,
            BigDecimal totalLoss,
            BigDecimal netProfit,
            BigDecimal totalReturn,
            
            // 위험 지표
            BigDecimal maxDrawdown,
            BigDecimal volatility,
            BigDecimal sharpeRatio,
            
            // 거래 통계
            BigDecimal avgWin,
            BigDecimal avgLoss,
            BigDecimal profitFactor,
            Integer maxConsecutiveWins,
            Integer maxConsecutiveLosses,
            
            // 시간 통계
            LocalDateTime bestPerformanceDate,
            LocalDateTime worstPerformanceDate,
            Long averageHoldingPeriod, // 분 단위
            
            LocalDateTime calculatedAt
    ) {
        /**
         * 손익비 계산
         */
        public BigDecimal getRiskRewardRatio() {
            if (avgLoss == null || avgLoss.compareTo(BigDecimal.ZERO) == 0) {
                return BigDecimal.ZERO;
            }
            
            return avgWin.divide(avgLoss.abs(), 4, java.math.RoundingMode.HALF_UP);
        }
    }

    /**
     * 자동매매 이벤트 로그 DTO
     *
     * 자동매매 실행 중 발생하는 이벤트 기록
     */
    @Builder
    public record EventLog(
            String id,
            String configId,
            String eventType,    // SIGNAL_RECEIVED, ORDER_PLACED, ORDER_FILLED, POSITION_OPENED, POSITION_CLOSED, ERROR
            String description,
            String symbol,
            Map<String, Object> details,
            LocalDateTime timestamp
    ) {}
}