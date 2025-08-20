package com.quantum.api.kiwoom.controller;

import com.quantum.api.kiwoom.dto.chart.timeseries.DailyChartRequest;
import com.quantum.api.kiwoom.dto.chart.timeseries.DailyChartResponse;
import com.quantum.api.kiwoom.dto.chart.timeseries.MinuteChartRequest;
import com.quantum.api.kiwoom.dto.chart.timeseries.MinuteChartResponse;
import com.quantum.api.kiwoom.dto.chart.timeseries.WeeklyChartRequest;
import com.quantum.api.kiwoom.dto.chart.timeseries.WeeklyChartResponse;
import com.quantum.api.kiwoom.dto.chart.timeseries.YearlyChartRequest;
import com.quantum.api.kiwoom.dto.chart.timeseries.YearlyChartResponse;
import com.quantum.api.kiwoom.dto.chart.realtime.TickChartRequest;
import com.quantum.api.kiwoom.dto.chart.realtime.TickChartResponse;
import com.quantum.api.kiwoom.dto.chart.sector.SectorTickChartRequest;
import com.quantum.api.kiwoom.dto.chart.sector.SectorTickChartResponse;
import com.quantum.api.kiwoom.dto.chart.investor.InvestorAnalysisRequest;
import com.quantum.api.kiwoom.dto.chart.investor.InvestorAnalysisResponse;
import com.quantum.api.kiwoom.dto.chart.analysis.OrderBookAnalysisRequest;
import com.quantum.api.kiwoom.dto.chart.analysis.OrderBookAnalysisResponse;

import com.quantum.api.kiwoom.service.chart.DailyChartService;
import com.quantum.api.kiwoom.service.chart.MinuteChartService;
import com.quantum.api.kiwoom.service.chart.WeeklyChartService;
import com.quantum.api.kiwoom.service.chart.YearlyChartService;
import com.quantum.api.kiwoom.service.chart.TickChartService;
import com.quantum.api.kiwoom.service.chart.SectorTickChartService;
import com.quantum.api.kiwoom.service.chart.InvestorAnalysisService;
import com.quantum.api.kiwoom.service.chart.OrderBookAnalysisService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 통합 차트 API 컨트롤러
 * 
 * 키움증권 차트 API 8개를 통합하여 제공하는 RESTful 컨트롤러
 * - 일봉차트 (ka10081), 분봉차트 (ka10080), 주봉차트 (ka10082), 년봉차트 (ka10094)
 * - 틱차트 (ka10079), 업종틱차트 (ka20004)
 * - 투자자기관별차트 (ka10060), 거래원매물대분석 (ka10043)
 * 
 * URL 매핑:
 * - /api/dostk/chart/ - 주식 차트 API
 * - /api/dostk/chart/sector/ - 업종 차트 API  
 * - /api/dostk/chart/institutional/ - 기관 관련 차트 API
 */
@RestController
@RequestMapping("/api/dostk/chart")
@RequiredArgsConstructor
@Validated
@Slf4j
@Tag(name = "Chart API", description = "키움증권 차트 데이터 조회 API")
public class ChartController {

    private final DailyChartService dailyChartService;
    private final MinuteChartService minuteChartService;
    private final WeeklyChartService weeklyChartService;
    private final YearlyChartService yearlyChartService;
    private final TickChartService tickChartService;
    private final SectorTickChartService sectorTickChartService;
    private final InvestorAnalysisService investorAnalysisService;
    private final OrderBookAnalysisService orderBookAnalysisService;

    // ===== 주식 일반 차트 API =====

    /**
     * 일봉 차트 조회 (ka10081)
     * 일/주/월/년봉 데이터 제공
     */
    @GetMapping(value = "/daily/{stockCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "일봉 차트 조회", 
        description = "종목의 일봉, 주봉, 월봉, 년봉 차트 데이터를 조회합니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "차트 조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (종목코드 오류 등)"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public Mono<DailyChartResponse> getDailyChart(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable @Pattern(regexp = "^[0-9A-Z]{6}$") String stockCode,
            
            @Parameter(description = "차트 유형 (D:일봉, W:주봉, M:월봉, Y:년봉)", example = "D")
            @RequestParam(defaultValue = "D") @Pattern(regexp = "^[DWMY]$") String periodType,
            
            @Parameter(description = "조회 개수 (1-2000)", example = "30")
            @RequestParam(defaultValue = "30") Integer dataCount,
            
            @Parameter(description = "시작일자 (YYYYMMDD)", example = "20240101")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String startDate,
            
            @Parameter(description = "종료일자 (YYYYMMDD)", example = "20241231")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String endDate,
            
            @Parameter(description = "수정주가 반영 여부", example = "true")
            @RequestParam(defaultValue = "true") Boolean adjustPrice) {

        log.info("일봉 차트 조회 요청 - 종목: {}, 유형: {}, 개수: {}", stockCode, periodType, dataCount);

        return dailyChartService.getDailyChart(stockCode, startDate != null ? startDate : "");
    }

    /**
     * 분봉 차트 조회 (ka10080)
     * 1분/3분/5분/10분/15분/30분/60분/120분 데이터 제공
     */
    @GetMapping(value = "/minute/{stockCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "분봉 차트 조회", 
        description = "종목의 분봉 차트 데이터를 다양한 시간 단위로 조회합니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "차트 조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (종목코드 오류 등)"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public Mono<MinuteChartResponse> getMinuteChart(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable @Pattern(regexp = "^[0-9A-Z]{6}$") String stockCode,
            
            @Parameter(description = "분 단위 (1,3,5,10,15,30,60,120)", example = "5")
            @RequestParam(defaultValue = "5") Integer minuteType,
            
            @Parameter(description = "조회 개수 (1-2000)", example = "100")
            @RequestParam(defaultValue = "100") Integer dataCount,
            
            @Parameter(description = "시작일자 (YYYYMMDD)", example = "20240101")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String startDate,
            
            @Parameter(description = "종료일자 (YYYYMMDD)", example = "20241231")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String endDate) {

        log.info("분봉 차트 조회 요청 - 종목: {}, 분단위: {}, 개수: {}", stockCode, minuteType, dataCount);

        return minuteChartService.getMinuteChart(stockCode, startDate != null ? startDate : "", minuteType.toString());
    }

    /**
     * 주봉 차트 조회 (ka10082)
     */
    @GetMapping(value = "/week/{stockCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "주봉 차트 조회", 
        description = "종목의 주봉 차트 데이터를 조회합니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "차트 조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (종목코드 오류 등)"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public Mono<WeeklyChartResponse> getWeekChart(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable @Pattern(regexp = "^[0-9A-Z]{6}$") String stockCode,
            
            @Parameter(description = "조회 개수 (1-2000)", example = "52")
            @RequestParam(defaultValue = "52") Integer dataCount,
            
            @Parameter(description = "시작일자 (YYYYMMDD)", example = "20240101")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String startDate,
            
            @Parameter(description = "종료일자 (YYYYMMDD)", example = "20241231")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String endDate) {

        log.info("주봉 차트 조회 요청 - 종목: {}, 개수: {}", stockCode, dataCount);

        return weeklyChartService.getWeeklyChart(stockCode, startDate != null ? startDate : "");
    }

    /**
     * 년봉 차트 조회 (ka10094)
     */
    @GetMapping(value = "/year/{stockCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "년봉 차트 조회", 
        description = "종목의 년봉 차트 데이터를 조회합니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "차트 조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (종목코드 오류 등)"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public Mono<YearlyChartResponse> getYearChart(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable @Pattern(regexp = "^[0-9A-Z]{6}$") String stockCode,
            
            @Parameter(description = "조회 개수 (1-20)", example = "10")
            @RequestParam(defaultValue = "10") Integer dataCount) {

        log.info("년봉 차트 조회 요청 - 종목: {}, 개수: {}", stockCode, dataCount);

        return yearlyChartService.getYearlyChart(stockCode, "");
    }

    /**
     * 틱 차트 조회 (ka10079)
     */
    @GetMapping(value = "/tick/{stockCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "틱 차트 조회", 
        description = "종목의 실시간 틱 데이터를 조회합니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "차트 조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (종목코드 오류 등)"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public Mono<TickChartResponse> getTickChart(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable @Pattern(regexp = "^[0-9A-Z]{6}$") String stockCode,
            
            @Parameter(description = "조회 개수 (1-2000)", example = "100")
            @RequestParam(defaultValue = "100") Integer dataCount,
            
            @Parameter(description = "조회 기준일 (YYYYMMDD)", example = "20240820")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String baseDate) {

        log.info("틱 차트 조회 요청 - 종목: {}, 개수: {}", stockCode, dataCount);

        return tickChartService.getTickChart(stockCode, baseDate != null ? baseDate : "");
    }

    // ===== 업종 차트 API =====

    /**
     * 업종 틱 차트 조회 (ka20004)
     */
    @GetMapping(value = "/sector/tick/{sectorCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "업종 틱 차트 조회", 
        description = "업종의 실시간 틱 데이터를 조회합니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "차트 조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (업종코드 오류 등)"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public Mono<SectorTickChartResponse> getSectorTickChart(
            @Parameter(description = "업종코드 (001:KOSPI종합, 101:KOSDAQ종합 등)", example = "001")
            @PathVariable @Pattern(regexp = "^[0-9]{3}$") String sectorCode,
            
            @Parameter(description = "조회 개수 (1-2000)", example = "100")
            @RequestParam(defaultValue = "100") Integer dataCount,
            
            @Parameter(description = "조회 기준일 (YYYYMMDD)", example = "20240820")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String baseDate) {

        log.info("업종 틱 차트 조회 요청 - 업종: {}, 개수: {}", sectorCode, dataCount);

        return sectorTickChartService.getSectorTickChart(sectorCode, baseDate != null ? baseDate : "");
    }

    // ===== 기관 투자자 차트 API =====

    /**
     * 투자자 기관별 차트 조회 (ka10060)
     */
    @GetMapping(value = "/institutional/{stockCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "투자자 기관별 차트 조회", 
        description = "종목별 투자자 유형별(외인, 기관, 개인) 매매동향을 차트로 조회합니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "차트 조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (종목코드 오류 등)"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public Mono<InvestorAnalysisResponse> getInstitutionalChart(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable @Pattern(regexp = "^[0-9A-Z]{6}$") String stockCode,
            
            @Parameter(description = "조회 개수 (1-2000)", example = "30")
            @RequestParam(defaultValue = "30") Integer dataCount,
            
            @Parameter(description = "시작일자 (YYYYMMDD)", example = "20240101")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String startDate,
            
            @Parameter(description = "종료일자 (YYYYMMDD)", example = "20241231")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String endDate) {

        log.info("투자자 기관별 차트 조회 요청 - 종목: {}, 개수: {}", stockCode, dataCount);

        return investorAnalysisService.getInvestorAnalysis(stockCode, startDate != null ? startDate : "", "D");
    }

    /**
     * 거래원 매물대 분석 조회 (ka10043)
     */
    @GetMapping(value = "/askbid/{stockCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "거래원 매물대 분석 조회", 
        description = "종목의 거래원별 매도/매수 잔량 분석 데이터를 조회합니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "분석 조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (종목코드 오류 등)"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    public Mono<OrderBookAnalysisResponse> getAskBidAnalysis(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable @Pattern(regexp = "^[0-9A-Z]{6}$") String stockCode,
            
            @Parameter(description = "조회 유형 (1:실시간, 2:일중)", example = "1")
            @RequestParam(defaultValue = "1") @Pattern(regexp = "^[12]$") String queryType,
            
            @Parameter(description = "조회 기준일 (YYYYMMDD)", example = "20240820")
            @RequestParam(required = false) @Pattern(regexp = "^[0-9]{8}$") String baseDate) {

        log.info("거래원 매물대 분석 조회 요청 - 종목: {}, 유형: {}", stockCode, queryType);

        return orderBookAnalysisService.getOrderBookAnalysis(stockCode, baseDate != null ? baseDate : "");
    }

    // ===== 편의 메서드 =====

    /**
     * 종목 전체 차트 요약 조회
     * 일봉, 분봉, 주봉 데이터를 한 번에 조회
     */
    @GetMapping(value = "/summary/{stockCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "종목 차트 요약 조회", 
        description = "종목의 주요 차트 데이터를 요약하여 한 번에 조회합니다. (일봉 30개, 분봉 100개, 주봉 52개)"
    )
    public Mono<Object> getChartSummary(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable @Pattern(regexp = "^[0-9A-Z]{6}$") String stockCode) {

        log.info("종목 차트 요약 조회 요청 - 종목: {}", stockCode);

        // 병렬로 차트 데이터 조회
        Mono<DailyChartResponse> dailyChart = dailyChartService.getDailyChart(stockCode, "");

        Mono<MinuteChartResponse> minuteChart = minuteChartService.getMinuteChart(stockCode, "", "5");

        Mono<WeeklyChartResponse> weekChart = weeklyChartService.getWeeklyChart(stockCode, "");

        // 결과 통합
        return Mono.zip(dailyChart, minuteChart, weekChart)
                .map(tuple -> {
                    return new Object() {
                        public final DailyChartResponse daily = tuple.getT1();
                        public final MinuteChartResponse minute = tuple.getT2();
                        public final WeeklyChartResponse week = tuple.getT3();
                        public final String requestStockCode = stockCode;
                        public final long timestamp = System.currentTimeMillis();
                    };
                });
    }

    /**
     * 실시간 차트 데이터 조회 (틱 + 분봉)
     */
    @GetMapping(value = "/realtime/{stockCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
        summary = "실시간 차트 데이터 조회", 
        description = "종목의 실시간 틱 데이터와 최신 분봉 데이터를 조회합니다."
    )
    public Mono<Object> getRealtimeChart(
            @Parameter(description = "종목코드 (6자리)", example = "005930")
            @PathVariable @Pattern(regexp = "^[0-9A-Z]{6}$") String stockCode) {

        log.info("실시간 차트 데이터 조회 요청 - 종목: {}", stockCode);

        // 틱 데이터와 1분봉 데이터를 병렬 조회
        Mono<TickChartResponse> tickChart = tickChartService.getTickChart(stockCode, "");

        Mono<MinuteChartResponse> minuteChart = minuteChartService.getMinuteChart(stockCode, "", "1");

        // 결과 통합
        return Mono.zip(tickChart, minuteChart)
                .map(tuple -> {
                    return new Object() {
                        public final TickChartResponse tick = tuple.getT1();
                        public final MinuteChartResponse minute = tuple.getT2();
                        public final String requestStockCode = stockCode;
                        public final long timestamp = System.currentTimeMillis();
                        public final String note = "실시간 데이터 (틱: 50개, 1분봉: 50개)";
                    };
                });
    }
}