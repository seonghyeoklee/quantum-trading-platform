package com.quantum.web.controller;

import com.quantum.web.dto.ApiResponse;
import com.quantum.web.service.PortfolioService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;


/**
 * Portfolio Controller
 *
 * 포트폴리오 관련 API를 제공하는 컨트롤러
 * - 포트폴리오 조회/생성
 * - 보유 포지션 조회
 * - 손익 현황 조회
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/portfolio")
@RequiredArgsConstructor
@Tag(name = "Portfolio", description = "포트폴리오 API")
public class PortfolioController {

    private final PortfolioService portfolioService;

    @Operation(
        summary = "포트폴리오 목록 조회",
        description = "사용자의 포트폴리오 목록을 조회합니다."
    )
    @GetMapping
    public ResponseEntity<ApiResponse<Object>> getPortfolios(
            @Parameter(description = "사용자 ID", example = "USER-123")
            @RequestParam String userId,

            @Parameter(description = "페이지 번호", example = "0")
            @RequestParam(defaultValue = "0")
            @Min(value = 0, message = "페이지 번호는 0 이상이어야 합니다")
            int page,

            @Parameter(description = "페이지 크기", example = "10")
            @RequestParam(defaultValue = "10")
            @Min(value = 1, message = "페이지 크기는 1 이상이어야 합니다")
            @Max(value = 50, message = "페이지 크기는 50 이하여야 합니다")
            int size
    ) {
        log.debug("Portfolios requested - userId: {}, page: {}, size: {}", userId, page, size);

        try {
            var portfolios = portfolioService.getPortfolios(userId, page, size);

            return ResponseEntity.ok(ApiResponse.success(portfolios,
                String.format("포트폴리오 목록 조회 완료 - %s", userId)));

        } catch (Exception e) {
            log.error("Failed to get portfolios for user: {}", userId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("포트폴리오 목록 조회 중 오류가 발생했습니다", "PORTFOLIOS_GET_ERROR"));
        }
    }

    @Operation(
        summary = "포트폴리오 상세 조회",
        description = "특정 포트폴리오의 상세 정보를 조회합니다."
    )
    @GetMapping("/{portfolioId}")
    public ResponseEntity<ApiResponse<Object>> getPortfolio(
            @Parameter(description = "포트폴리오 ID", example = "PORTFOLIO-123")
            @PathVariable String portfolioId
    ) {
        log.debug("Portfolio detail requested - portfolioId: {}", portfolioId);

        try {
            var portfolio = portfolioService.getPortfolio(portfolioId);

            if (portfolio == null) {
                return ResponseEntity.notFound().build();
            }

            return ResponseEntity.ok(ApiResponse.success(portfolio,
                String.format("포트폴리오 상세 조회 완료 - %s", portfolioId)));

        } catch (Exception e) {
            log.error("Failed to get portfolio: {}", portfolioId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("포트폴리오 상세 조회 중 오류가 발생했습니다", "PORTFOLIO_GET_ERROR"));
        }
    }

    @Operation(
        summary = "포트폴리오 보유 종목 조회",
        description = "포트폴리오의 보유 종목(포지션) 목록을 조회합니다."
    )
    @GetMapping("/{portfolioId}/positions")
    public ResponseEntity<ApiResponse<Object>> getPositions(
            @Parameter(description = "포트폴리오 ID", example = "PORTFOLIO-123")
            @PathVariable String portfolioId,

            @Parameter(description = "종목 코드 필터", example = "005930")
            @RequestParam(required = false) String symbol,

            @Parameter(description = "최소 보유량 필터", example = "0")
            @RequestParam(defaultValue = "0")
            @Min(value = 0, message = "최소 보유량은 0 이상이어야 합니다")
            int minQuantity
    ) {
        log.debug("Positions requested - portfolioId: {}, symbol: {}, minQuantity: {}",
                 portfolioId, symbol, minQuantity);

        try {
            var positions = portfolioService.getPositions(portfolioId, symbol, minQuantity);

            return ResponseEntity.ok(ApiResponse.success(positions,
                String.format("포지션 목록 조회 완료 - %s", portfolioId)));

        } catch (Exception e) {
            log.error("Failed to get positions for portfolio: {}", portfolioId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("포지션 목록 조회 중 오류가 발생했습니다", "POSITIONS_GET_ERROR"));
        }
    }

    @Operation(
        summary = "포트폴리오 손익 현황 조회",
        description = "포트폴리오의 실현/미실현 손익 현황을 조회합니다."
    )
    @GetMapping("/{portfolioId}/pnl")
    public ResponseEntity<ApiResponse<Object>> getPnL(
            @Parameter(description = "포트폴리오 ID", example = "PORTFOLIO-123")
            @PathVariable String portfolioId,

            @Parameter(description = "기간 (일)", example = "30")
            @RequestParam(defaultValue = "30")
            @Min(value = 1, message = "기간은 1일 이상이어야 합니다")
            @Max(value = 365, message = "기간은 365일 이하여야 합니다")
            int periodDays,

            @Parameter(description = "그룹화 단위", example = "daily")
            @RequestParam(defaultValue = "daily")
            @Pattern(regexp = "^(daily|weekly|monthly)$", message = "그룹화 단위는 daily, weekly, monthly 중 하나여야 합니다")
            String groupBy
    ) {
        log.debug("P&L requested - portfolioId: {}, periodDays: {}, groupBy: {}",
                 portfolioId, periodDays, groupBy);

        try {
            var pnl = portfolioService.getPnL(portfolioId, periodDays, groupBy);

            return ResponseEntity.ok(ApiResponse.success(pnl,
                String.format("손익 현황 조회 완료 - %s", portfolioId)));

        } catch (Exception e) {
            log.error("Failed to get P&L for portfolio: {}", portfolioId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("손익 현황 조회 중 오류가 발생했습니다", "PNL_GET_ERROR"));
        }
    }

    @Operation(
        summary = "포트폴리오 성과 분석",
        description = "포트폴리오의 성과 지표를 분석합니다 (샤프 지수, 변동성 등)."
    )
    @GetMapping("/{portfolioId}/performance")
    public ResponseEntity<ApiResponse<Object>> getPerformance(
            @Parameter(description = "포트폴리오 ID", example = "PORTFOLIO-123")
            @PathVariable String portfolioId,

            @Parameter(description = "분석 기간 (일)", example = "90")
            @RequestParam(defaultValue = "90")
            @Min(value = 30, message = "분석 기간은 30일 이상이어야 합니다")
            @Max(value = 365, message = "분석 기간은 365일 이하여야 합니다")
            int periodDays,

            @Parameter(description = "벤치마크 지수", example = "KOSPI")
            @RequestParam(defaultValue = "KOSPI")
            @Pattern(regexp = "^(KOSPI|KOSDAQ|KRX100)$", message = "지원되지 않는 벤치마크입니다")
            String benchmark
    ) {
        log.debug("Performance analysis requested - portfolioId: {}, periodDays: {}, benchmark: {}",
                 portfolioId, periodDays, benchmark);

        try {
            var performance = portfolioService.getPerformanceAnalysis(portfolioId, periodDays, benchmark);

            return ResponseEntity.ok(ApiResponse.success(performance,
                String.format("성과 분석 완료 - %s", portfolioId)));

        } catch (Exception e) {
            log.error("Failed to get performance analysis for portfolio: {}", portfolioId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("성과 분석 중 오류가 발생했습니다", "PERFORMANCE_GET_ERROR"));
        }
    }

    @Operation(
        summary = "포트폴리오 리밸런싱 제안",
        description = "포트폴리오 리밸런싱을 위한 제안을 생성합니다."
    )
    @GetMapping("/{portfolioId}/rebalance")
    public ResponseEntity<ApiResponse<Object>> getRebalanceSuggestion(
            @Parameter(description = "포트폴리오 ID", example = "PORTFOLIO-123")
            @PathVariable String portfolioId,

            @Parameter(description = "목표 리스크 레벨", example = "moderate")
            @RequestParam(defaultValue = "moderate")
            @Pattern(regexp = "^(conservative|moderate|aggressive)$", message = "리스크 레벨은 conservative, moderate, aggressive 중 하나여야 합니다")
            String riskLevel
    ) {
        log.debug("Rebalance suggestion requested - portfolioId: {}, riskLevel: {}", portfolioId, riskLevel);

        try {
            var rebalanceSuggestion = portfolioService.getRebalanceSuggestion(portfolioId, riskLevel);

            return ResponseEntity.ok(ApiResponse.success(rebalanceSuggestion,
                String.format("리밸런싱 제안 생성 완료 - %s", portfolioId)));

        } catch (Exception e) {
            log.error("Failed to get rebalance suggestion for portfolio: {}", portfolioId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("리밸런싱 제안 생성 중 오류가 발생했습니다", "REBALANCE_GET_ERROR"));
        }
    }

    @Operation(
        summary = "포트폴리오 구독 정보",
        description = "WebSocket을 통한 실시간 포트폴리오 업데이트 구독 정보를 제공합니다."
    )
    @GetMapping("/{portfolioId}/subscribe")
    public ResponseEntity<ApiResponse<Object>> getSubscriptionInfo(
            @Parameter(description = "포트폴리오 ID", example = "PORTFOLIO-123")
            @PathVariable String portfolioId
    ) {
        log.debug("Portfolio subscription info requested - portfolioId: {}", portfolioId);

        return ResponseEntity.ok(ApiResponse.success(
            new SubscriptionInfo(
                String.format("/topic/portfolio/%s", portfolioId),
                String.format("/topic/positions/%s", portfolioId),
                "ws://localhost:10101/api/v1/ws"
            ),
            "구독 정보 제공 완료"
        ));
    }

    // Inner class for subscription info response
    public record SubscriptionInfo(
        String portfolioTopic,
        String positionsTopic,
        String websocketUrl
    ) {}
}
