package com.quantum.web.controller;

import com.quantum.web.dto.ApiResponse;
import com.quantum.web.dto.ChartDataResponse;
import com.quantum.web.service.ChartDataService;
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
 * Chart Data Controller
 *
 * 차트 데이터 API를 제공하는 컨트롤러
 * - 캔들스틱 차트 데이터
 * - 기술지표 데이터
 * - 실시간 차트 업데이트
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/charts")
@RequiredArgsConstructor
@Tag(name = "Chart", description = "차트 데이터 API")
public class ChartController {

    private final ChartDataService chartDataService;

    @Operation(
        summary = "차트 데이터 조회",
        description = "지정된 종목의 캔들스틱 차트 데이터를 조회합니다."
    )
    @GetMapping("/{symbol}")
    public ResponseEntity<ApiResponse<ChartDataResponse>> getChartData(
            @Parameter(description = "종목 코드 (6자리)", example = "005930")
            @PathVariable
            @Pattern(regexp = "^[A-Z0-9]{6}$", message = "종목 코드는 6자리 영숫자여야 합니다")
            String symbol,

            @Parameter(description = "시간 프레임", example = "1d")
            @RequestParam(defaultValue = "1d")
            @Pattern(regexp = "^(1m|5m|15m|30m|1h|4h|1d|1w|1M)$", message = "유효하지 않은 시간 프레임입니다")
            String timeframe,

            @Parameter(description = "데이터 개수 (최대 1000)", example = "100")
            @RequestParam(defaultValue = "100")
            @Min(value = 1, message = "최소 1개의 데이터가 필요합니다")
            @Max(value = 1000, message = "최대 1000개의 데이터만 조회할 수 있습니다")
            int limit
    ) {
        log.debug("Chart data requested - symbol: {}, timeframe: {}, limit: {}", symbol, timeframe, limit);

        try {
            ChartDataResponse chartData = chartDataService.getChartData(symbol, timeframe, limit);

            return ResponseEntity.ok(ApiResponse.success(chartData,
                String.format("차트 데이터 조회 완료 - %s (%s)", symbol, timeframe)));

        } catch (Exception e) {
            log.error("Failed to get chart data for symbol: {}, timeframe: {}", symbol, timeframe, e);

            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("차트 데이터 조회 중 오류가 발생했습니다", "CHART_DATA_ERROR"));
        }
    }

    @Operation(
        summary = "실시간 차트 데이터 구독",
        description = "WebSocket을 통한 실시간 차트 데이터 구독을 위한 엔드포인트 정보를 제공합니다."
    )
    @GetMapping("/{symbol}/subscribe")
    public ResponseEntity<ApiResponse<Object>> getSubscriptionInfo(
            @Parameter(description = "종목 코드", example = "005930")
            @PathVariable String symbol
    ) {
        log.debug("Subscription info requested for symbol: {}", symbol);

        return ResponseEntity.ok(ApiResponse.success(
            new SubscriptionInfo(
                String.format("/topic/charts/%s", symbol),
                String.format("ws://localhost:8080/api/v1/ws")
            ),
            "구독 정보 제공 완료"
        ));
    }

    @Operation(
        summary = "종목 검색",
        description = "종목 코드나 회사명으로 종목을 검색합니다."
    )
    @GetMapping("/search")
    public ResponseEntity<ApiResponse<Object>> searchSymbols(
            @Parameter(description = "검색 키워드", example = "삼성")
            @RequestParam String keyword,

            @Parameter(description = "검색 결과 개수", example = "10")
            @RequestParam(defaultValue = "10")
            @Max(value = 50, message = "최대 50개의 결과만 조회할 수 있습니다")
            int limit
    ) {
        log.debug("Symbol search requested - keyword: {}, limit: {}", keyword, limit);

        try {
            var searchResults = chartDataService.searchSymbols(keyword, limit);

            return ResponseEntity.ok(ApiResponse.success(searchResults,
                String.format("종목 검색 완료 - '%s'", keyword)));

        } catch (Exception e) {
            log.error("Failed to search symbols for keyword: {}", keyword, e);

            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("종목 검색 중 오류가 발생했습니다", "SYMBOL_SEARCH_ERROR"));
        }
    }

    @Operation(
        summary = "기술지표 데이터 조회",
        description = "지정된 종목의 기술지표 데이터를 조회합니다."
    )
    @GetMapping("/{symbol}/indicators")
    public ResponseEntity<ApiResponse<Object>> getIndicatorData(
            @Parameter(description = "종목 코드", example = "005930")
            @PathVariable String symbol,

            @Parameter(description = "지표 종류", example = "RSI")
            @RequestParam
            @Pattern(regexp = "^(MA|EMA|RSI|MACD|BOLLINGER_BANDS)$", message = "지원되지 않는 지표입니다")
            String indicator,

            @Parameter(description = "지표 기간", example = "14")
            @RequestParam(defaultValue = "14")
            @Min(value = 1, message = "기간은 1 이상이어야 합니다")
            @Max(value = 200, message = "기간은 200 이하여야 합니다")
            int period,

            @Parameter(description = "데이터 개수", example = "100")
            @RequestParam(defaultValue = "100")
            @Max(value = 1000, message = "최대 1000개의 데이터만 조회할 수 있습니다")
            int limit
    ) {
        log.debug("Indicator data requested - symbol: {}, indicator: {}, period: {}, limit: {}",
                 symbol, indicator, period, limit);

        try {
            var indicatorData = chartDataService.getIndicatorData(symbol, indicator, period, limit);

            return ResponseEntity.ok(ApiResponse.success(indicatorData,
                String.format("기술지표 데이터 조회 완료 - %s %s(%d)", symbol, indicator, period)));

        } catch (Exception e) {
            log.error("Failed to get indicator data for symbol: {}, indicator: {}", symbol, indicator, e);

            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("기술지표 데이터 조회 중 오류가 발생했습니다", "INDICATOR_DATA_ERROR"));
        }
    }

    // Inner class for subscription info response
    public record SubscriptionInfo(String topic, String websocketUrl) {}
}
