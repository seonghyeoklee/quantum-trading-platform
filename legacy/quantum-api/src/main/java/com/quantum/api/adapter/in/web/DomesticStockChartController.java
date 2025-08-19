package com.quantum.api.adapter.in.web;

import com.quantum.core.domain.model.analysis.TechnicalIndicatorResult;
import com.quantum.core.domain.model.common.TechnicalIndicatorType;
import com.quantum.core.domain.model.common.TimeframeCode;
import com.quantum.kis.model.KisStockCandleResponse;
import com.quantum.kis.service.KisCandleDataService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * 국내주식 차트 분석 API 컨트롤러
 *
 * <p>KIS API를 통한 캔들 데이터 조회 및 기술적 분석 기능 제공
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/chart/domestic")
@RequiredArgsConstructor
@Tag(name = "Domestic Stock Chart", description = "국내주식 차트 분석 API")
public class DomesticStockChartController {

    private final KisCandleDataService kisCandleDataService;

    // TODO: TechnicalAnalysisService 주입 필요 (구현 후)

    /**
     * 국내주식 일봉 데이터 조회
     *
     * @param stockCode 종목코드 (6자리)
     * @param startDate 조회 시작일
     * @param endDate 조회 종료일
     * @param adjustedPrice 수정주가 적용 여부 (기본: false)
     * @return 일봉 캔들 데이터
     */
    @GetMapping("/{stockCode}/daily")
    @Operation(summary = "국내주식 일봉 데이터 조회", description = "지정된 기간의 국내주식 일봉 캔들 데이터를 조회합니다.")
    public ResponseEntity<KisStockCandleResponse> getDailyCandleData(
            @Parameter(description = "종목코드 (6자리)", example = "005930") @PathVariable
                    String stockCode,
            @Parameter(description = "조회 시작일", example = "2024-01-01")
                    @RequestParam
                    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
                    LocalDate startDate,
            @Parameter(description = "조회 종료일", example = "2024-12-31")
                    @RequestParam
                    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
                    LocalDate endDate,
            @Parameter(description = "수정주가 적용 여부", example = "false")
                    @RequestParam(defaultValue = "false")
                    boolean adjustedPrice) {

        log.info(
                "Requesting daily candle data for {} from {} to {}", stockCode, startDate, endDate);

        KisStockCandleResponse response =
                kisCandleDataService.getDailyCandleData(
                        stockCode, startDate, endDate, adjustedPrice);

        return ResponseEntity.ok(response);
    }

    /** 국내주식 주봉 데이터 조회 */
    @GetMapping("/{stockCode}/weekly")
    @Operation(summary = "국내주식 주봉 데이터 조회", description = "지정된 기간의 국내주식 주봉 캔들 데이터를 조회합니다.")
    public ResponseEntity<KisStockCandleResponse> getWeeklyCandleData(
            @PathVariable String stockCode,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate,
            @RequestParam(defaultValue = "false") boolean adjustedPrice) {

        log.info(
                "Requesting weekly candle data for {} from {} to {}",
                stockCode,
                startDate,
                endDate);

        KisStockCandleResponse response =
                kisCandleDataService.getWeeklyCandleData(
                        stockCode, startDate, endDate, adjustedPrice);

        return ResponseEntity.ok(response);
    }

    /** 국내주식 월봉 데이터 조회 */
    @GetMapping("/{stockCode}/monthly")
    @Operation(summary = "국내주식 월봉 데이터 조회", description = "지정된 기간의 국내주식 월봉 캔들 데이터를 조회합니다.")
    public ResponseEntity<KisStockCandleResponse> getMonthlyCandleData(
            @PathVariable String stockCode,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate,
            @RequestParam(defaultValue = "false") boolean adjustedPrice) {

        log.info(
                "Requesting monthly candle data for {} from {} to {}",
                stockCode,
                startDate,
                endDate);

        KisStockCandleResponse response =
                kisCandleDataService.getMonthlyCandleData(
                        stockCode, startDate, endDate, adjustedPrice);

        return ResponseEntity.ok(response);
    }

    /** 국내주식 분봉 데이터 조회 */
    @GetMapping("/{stockCode}/intraday")
    @Operation(summary = "국내주식 분봉 데이터 조회", description = "지정된 기간의 국내주식 분봉 캔들 데이터를 조회합니다.")
    public ResponseEntity<KisStockCandleResponse> getIntradayCandleData(
            @PathVariable String stockCode,
            @Parameter(description = "분봉 시간프레임", example = "ONE_MINUTE") @RequestParam
                    TimeframeCode timeframe,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {

        log.info(
                "Requesting {} candle data for {} from {} to {}",
                timeframe.getKoreanName(),
                stockCode,
                startDate,
                endDate);

        KisStockCandleResponse response =
                kisCandleDataService.getIntradayCandleData(
                        stockCode, timeframe.name(), startDate, endDate);

        return ResponseEntity.ok(response);
    }

    /** 최근 N개 캔들 데이터 조회 */
    @GetMapping("/{stockCode}/recent")
    @Operation(summary = "최근 캔들 데이터 조회", description = "종목의 최근 N개 캔들 데이터를 조회합니다.")
    public ResponseEntity<KisStockCandleResponse> getRecentCandleData(
            @PathVariable String stockCode,
            @Parameter(description = "시간프레임", example = "ONE_DAY") @RequestParam
                    TimeframeCode timeframe,
            @Parameter(description = "조회할 캔들 개수", example = "20") @RequestParam(defaultValue = "20")
                    int count) {

        log.info(
                "Requesting recent {} {} candles for {}",
                count,
                timeframe.getKoreanName(),
                stockCode);

        KisStockCandleResponse response =
                kisCandleDataService.getRecentCandleData(stockCode, timeframe.name(), count);

        return ResponseEntity.ok(response);
    }

    /** 기술적 지표 계산 (단일 지표) */
    @PostMapping("/{stockCode}/indicators/{indicatorType}")
    @Operation(summary = "기술적 지표 계산", description = "캔들 데이터 기반으로 지정된 기술적 지표를 계산합니다.")
    public ResponseEntity<TechnicalIndicatorResult> calculateTechnicalIndicator(
            @PathVariable String stockCode,
            @Parameter(description = "기술적 지표 타입", example = "RSI") @PathVariable
                    TechnicalIndicatorType indicatorType,
            @Parameter(description = "시간프레임", example = "ONE_DAY") @RequestParam
                    TimeframeCode timeframe,
            @Parameter(description = "계산 파라미터 (JSON)", example = "{\"period\": 14}")
                    @RequestBody(required = false)
                    Map<String, Object> parameters) {

        log.info(
                "Calculating {} indicator for {} on {} timeframe",
                indicatorType.getKoreanName(),
                stockCode,
                timeframe.getKoreanName());

        // TODO: TechnicalAnalysisService 구현 후 연동
        log.warn("Technical indicator calculation not yet implemented");

        // 임시 응답
        TechnicalIndicatorResult result =
                TechnicalIndicatorResult.builder()
                        .symbol(stockCode)
                        .indicatorType(indicatorType)
                        .timeframe(timeframe)
                        .signal("HOLD")
                        .confidenceScore(java.math.BigDecimal.valueOf(50))
                        .build();

        return ResponseEntity.ok(result);
    }

    /** 종합 기술적 분석 */
    @PostMapping("/{stockCode}/analysis/comprehensive")
    @Operation(summary = "종합 기술적 분석", description = "여러 기술적 지표를 통한 종합적인 매매 신호를 생성합니다.")
    public ResponseEntity<Map<String, Object>> getComprehensiveAnalysis(
            @PathVariable String stockCode,
            @RequestParam TimeframeCode timeframe,
            @Parameter(description = "분석할 지표 목록") @RequestBody(required = false)
                    List<TechnicalIndicatorType> indicatorTypes) {

        log.info(
                "Performing comprehensive analysis for {} on {} timeframe",
                stockCode,
                timeframe.getKoreanName());

        // TODO: TechnicalAnalysisService 구현 후 연동
        log.warn("Comprehensive analysis not yet implemented");

        // 임시 응답
        Map<String, Object> analysis =
                Map.of(
                        "symbol",
                        stockCode,
                        "timeframe",
                        timeframe.getKoreanName(),
                        "overallSignal",
                        "HOLD",
                        "confidence",
                        50,
                        "indicators",
                        List.of(),
                        "timestamp",
                        java.time.LocalDateTime.now());

        return ResponseEntity.ok(analysis);
    }

    /** Rate Limit 상태 확인 */
    @GetMapping("/rate-limit-status")
    @Operation(
            summary = "API Rate Limit 상태 확인",
            description = "캔들 데이터 조회 API의 Rate Limit 현재 상태를 확인합니다.")
    public ResponseEntity<Map<String, Object>> getRateLimitStatus(
            @RequestParam(defaultValue = "ONE_DAY") TimeframeCode timeframe) {

        var status = kisCandleDataService.getRateLimitStatus(timeframe.name());

        Map<String, Object> response =
                Map.of(
                        "timeframe", timeframe.getKoreanName(),
                        "apiEndpoint", status.apiEndpoint(),
                        "callsLastSecond", status.callsLastSecond(),
                        "callsLastMinute", status.callsLastMinute(),
                        "callsLastHour", status.callsLastHour(),
                        "available", status.available());

        return ResponseEntity.ok(response);
    }
}
