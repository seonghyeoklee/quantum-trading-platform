package com.quantum.api.kiwoom.controller;

import com.quantum.api.kiwoom.dto.sector.chart.SectorDailyChartResponse;
import com.quantum.api.kiwoom.dto.sector.chart.SectorMinuteChartResponse;
import com.quantum.api.kiwoom.dto.sector.info.AllSectorIndicesResponse;
import com.quantum.api.kiwoom.dto.sector.info.SectorCurrentPriceResponse;
import com.quantum.api.kiwoom.dto.sector.info.SectorDailyDetailResponse;
import com.quantum.api.kiwoom.dto.sector.info.SectorStockPricesResponse;
import com.quantum.api.kiwoom.service.sector.AllSectorIndicesService;
import com.quantum.api.kiwoom.service.sector.SectorCurrentPriceService;
import com.quantum.api.kiwoom.service.sector.SectorDailyChartService;
import com.quantum.api.kiwoom.service.sector.SectorDailyDetailService;
import com.quantum.api.kiwoom.service.sector.SectorMinuteChartService;
import com.quantum.api.kiwoom.service.sector.SectorStockPricesService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.ExampleObject;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 업종 관련 REST API 컨트롤러
 * 키움증권 업종 API (ka20001~ka20009)를 RESTful 방식으로 제공
 */
@RestController
@RequestMapping("/api/sectors")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "업종 API", description = "업종 시세, 차트, 통계 정보 조회 API")
public class SectorController {
    
    private final SectorCurrentPriceService sectorCurrentPriceService;
    private final SectorStockPricesService sectorStockPricesService;
    private final AllSectorIndicesService allSectorIndicesService;
    private final SectorMinuteChartService sectorMinuteChartService;
    private final SectorDailyChartService sectorDailyChartService;
    private final SectorDailyDetailService sectorDailyDetailService;
    
    // ========== 업종 정보 조회 API ==========
    
    @Operation(
        summary = "업종 현재가 조회",
        description = """
            특정 업종의 실시간 현재가 정보를 조회합니다.
            
            **주요 기능:**
            - 업종 지수 현재가, 등락률, 거래량
            - 업종 내 주요 종목 정보
            - 시가총액, 거래대금 통계
            
            **업종코드 예시:**
            - 001: 종합(KOSPI)
            - 101: 종합(KOSDAQ)  
            - 201: KOSPI200
            """,
        tags = {"업종 정보"}
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 업종코드"),
        @ApiResponse(responseCode = "500", description = "서버 오류")
    })
    @GetMapping(value = "/current/{sectorCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<SectorCurrentPriceResponse> getCurrentPrice(
            @Parameter(description = "업종코드 (001:KOSPI, 101:KOSDAQ, 201:KOSPI200)", example = "001")
            @PathVariable String sectorCode,
            
            @Parameter(description = "조회할 종목 수 (1~40)", example = "20")
            @RequestParam(defaultValue = "20") Integer stockCount,
            
            @Parameter(description = "정렬기준 (MARKET_CAP:시총, TRADING_VALUE:거래대금, CHANGE_RATE:등락률)")
            @RequestParam(defaultValue = "MARKET_CAP") String sortBy) {
        
        log.info("업종현재가 조회 요청: 업종코드={}, 종목수={}, 정렬={}", sectorCode, stockCount, sortBy);
        
        // 기본 파라미터 설정
        String marketType = "0"; // KOSPI 기본
        String searchScope = "2"; // 업종지수 + 상위종목
        
        // 업종코드에 따라 시장구분 자동 설정
        if (sectorCode.startsWith("1")) {
            marketType = "1"; // KOSDAQ
        } else if (sectorCode.startsWith("2")) {
            marketType = "2"; // KOSPI200
        }
        
        return sectorCurrentPriceService.getSectorCurrentPrice(
            sectorCode, marketType, searchScope, stockCount.toString());
    }
    
    @Operation(
        summary = "업종별 주가 조회",
        description = """
            특정 업종에 속한 개별 종목들의 주가 정보를 조회합니다.
            
            **주요 기능:**
            - 업종 내 전체 종목 목록
            - 종목별 현재가, 등락률, 거래량
            - 다양한 정렬 옵션 지원
            - 페이징 처리 지원
            """,
        tags = {"업종 정보"}
    )
    @GetMapping(value = "/stocks/{sectorCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<SectorStockPricesResponse> getSectorStocks(
            @Parameter(description = "업종코드", example = "001")
            @PathVariable String sectorCode,
            
            @Parameter(description = "정렬기준 (NAME:종목명, MARKET_CAP:시총, CHANGE_RATE:등락률, TRADING_VALUE:거래대금)")
            @RequestParam(defaultValue = "MARKET_CAP") String sortBy,
            
            @Parameter(description = "페이지 크기 (1~100)", example = "50")
            @RequestParam(defaultValue = "50") Integer pageSize) {
        
        log.info("업종별주가 조회 요청: 업종코드={}, 정렬={}, 페이지크기={}", sectorCode, sortBy, pageSize);
        
        // 기본 파라미터 설정
        String marketType = "0"; // KOSPI 기본
        String sortType = "1"; // 기본 정렬
        String orderDirection = "D"; // 내림차순
        String stockCountStr = pageSize.toString();
        
        // 업종코드에 따라 시장구분 자동 설정
        if (sectorCode.startsWith("1")) {
            marketType = "1"; // KOSDAQ
        } else if (sectorCode.startsWith("2")) {
            marketType = "2"; // KOSPI200
        }
        
        // 정렬 기준에 따라 적절한 메서드 호출
        switch (sortBy.toUpperCase()) {
            case "NAME":
                return sectorStockPricesService.getStocksByName(sectorCode, marketType, pageSize, true);
            case "MARKET_CAP":
                return sectorStockPricesService.getTopStocksByMarketCap(sectorCode, marketType, pageSize);
            case "CHANGE_RATE":
                return sectorStockPricesService.getStocksByChangeRate(sectorCode, marketType, pageSize, true);
            case "TRADING_VALUE":
                return sectorStockPricesService.getTopStocksByTradingValue(sectorCode, marketType, pageSize);
            default:
                return sectorStockPricesService.getSectorStockPrices(
                    sectorCode, marketType, sortType, orderDirection, stockCountStr, "1");
        }
    }
    
    @Operation(
        summary = "전 업종 지수 현황",
        description = """
            전체 업종의 지수 현황을 한번에 조회합니다.
            
            **주요 기능:**
            - KOSPI, KOSDAQ, KOSPI200 등 주요 지수
            - 업종별 등락률, 거래량 현황
            - 시장 전체 동향 파악
            """,
        tags = {"업종 정보"}
    )
    @GetMapping(value = "/indices", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<AllSectorIndicesResponse> getAllIndices(
            @Parameter(description = "시장구분 (0:KOSPI, 1:KOSDAQ, 2:KOSPI200, ALL:전체)")
            @RequestParam(defaultValue = "ALL") String marketType) {
        
        log.info("전업종지수 조회 요청: 시장구분={}", marketType);
        
        String sortType = "1"; // 지수순
        String sortOrder = "1"; // 내림차순
        String categoryType = "1"; // 전체
        
        if ("ALL".equalsIgnoreCase(marketType)) {
            return allSectorIndicesService.getAllSectorIndices("9", sortType, sortOrder, categoryType);
        } else {
            return allSectorIndicesService.getAllSectorIndices(marketType, sortType, sortOrder, categoryType);
        }
    }
    
    // ========== 업종 차트 조회 API ==========
    
    @Operation(
        summary = "업종 분봉 차트 조회",
        description = """
            업종의 분봉 차트 데이터를 조회합니다.
            
            **지원 분봉:**
            - 1분봉, 3분봉, 5분봉, 10분봉, 30분봉, 60분봉
            
            **조회 기간:**
            - 최대 30일간 데이터 제공
            - 기간 미지정시 당일 데이터
            """,
        tags = {"업종 차트"}
    )
    @GetMapping(value = "/charts/minute/{sectorCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<SectorMinuteChartResponse> getMinuteChart(
            @Parameter(description = "업종코드", example = "001")
            @PathVariable String sectorCode,
            
            @Parameter(description = "분봉구분 (1,3,5,10,30,60)", example = "5")
            @RequestParam(defaultValue = "5") Integer minuteType,
            
            @Parameter(description = "조회시작일 (YYYYMMDD)", example = "20240101")
            @RequestParam(required = false) String fromDate,
            
            @Parameter(description = "조회종료일 (YYYYMMDD)", example = "20240131")
            @RequestParam(required = false) String toDate,
            
            @Parameter(description = "조회일수 (fromDate 대신 사용)", example = "7")
            @RequestParam(required = false) Integer days) {
        
        log.info("업종분봉차트 조회 요청: 업종코드={}, 분봉구분={}분, 시작일={}, 종료일={}, 일수={}", 
                 sectorCode, minuteType, fromDate, toDate, days);
        
        // 일수 기준 조회
        if (days != null && days > 0) {
            return sectorMinuteChartService.getRecentMinuteChart(sectorCode, minuteType, days);
        }
        
        // 기간 지정 조회
        if (fromDate != null && toDate != null) {
            return sectorMinuteChartService.getCustomMinuteChart(sectorCode, minuteType, fromDate, toDate);
        }
        
        // 당일 조회 (기본)
        return sectorMinuteChartService.getTodayMinuteChart(sectorCode, minuteType);
    }
    
    @Operation(
        summary = "업종 일봉 차트 조회",
        description = """
            업종의 일봉 차트 데이터를 조회합니다.
            
            **지원 기간:**
            - 일봉(D), 주봉(W), 월봉(M)
            
            **조회 옵션:**
            - 최근 N일/주/월
            - 특정 기간 지정
            - 년도별, 분기별 조회
            """,
        tags = {"업종 차트"}
    )
    @GetMapping(value = "/charts/daily/{sectorCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<SectorDailyChartResponse> getDailyChart(
            @Parameter(description = "업종코드", example = "001")
            @PathVariable String sectorCode,
            
            @Parameter(description = "기간구분 (D:일봉, W:주봉, M:월봉)", example = "D")
            @RequestParam(defaultValue = "D") String periodType,
            
            @Parameter(description = "조회시작일 (YYYYMMDD)")
            @RequestParam(required = false) String fromDate,
            
            @Parameter(description = "조회종료일 (YYYYMMDD)")
            @RequestParam(required = false) String toDate,
            
            @Parameter(description = "조회일수 (기본: 30일)", example = "90")
            @RequestParam(required = false) Integer days,
            
            @Parameter(description = "프리셋 기간 (week:금주, month:금월, quarter:분기, year:금년)")
            @RequestParam(required = false) String preset) {
        
        log.info("업종일봉차트 조회 요청: 업종코드={}, 기간구분={}, 프리셋={}", sectorCode, periodType, preset);
        
        // 프리셋 기간 조회
        if (preset != null) {
            switch (preset.toLowerCase()) {
                case "week":
                    return sectorDailyChartService.getRecentDailyChart(sectorCode, 7);
                case "month":
                    return sectorDailyChartService.getRecentDailyChart(sectorCode, 30);
                case "quarter":
                    return sectorDailyChartService.getRecentDailyChart(sectorCode, 90);
                case "year":
                    return sectorDailyChartService.getYearToDateChart(sectorCode);
                default:
                    break;
            }
        }
        
        // 일수 기준 조회
        if (days != null && days > 0) {
            switch (periodType.toUpperCase()) {
                case "W":
                    return sectorDailyChartService.getRecentWeeklyChart(sectorCode, days / 7);
                case "M":
                    return sectorDailyChartService.getRecentMonthlyChart(sectorCode, days / 30);
                default:
                    return sectorDailyChartService.getRecentDailyChart(sectorCode, days);
            }
        }
        
        // 기간 지정 조회
        if (fromDate != null && toDate != null) {
            switch (periodType.toUpperCase()) {
                case "W":
                    return sectorDailyChartService.getWeeklyChart(sectorCode, fromDate, toDate);
                case "M":
                    return sectorDailyChartService.getMonthlyChart(sectorCode, fromDate, toDate);
                default:
                    return sectorDailyChartService.getDailyChart(sectorCode, fromDate, toDate);
            }
        }
        
        // 기본 조회 (최근 30일)
        return sectorDailyChartService.getRecentDailyChart(sectorCode, 30);
    }
    
    // ========== 업종 상세 정보 API ==========
    
    @Operation(
        summary = "업종 일별 상세 정보 조회",
        description = """
            업종의 일별 상세 통계 정보를 조회합니다.
            
            **제공 정보:**
            - 일별 OHLC 데이터
            - 상승/하락/보합 종목 수 통계
            - 상한/하한 종목 수
            - 평균 등락률
            - 거래량/거래대금 통계
            """,
        tags = {"업종 상세"}
    )
    @GetMapping(value = "/details/daily/{sectorCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<SectorDailyDetailResponse> getDailyDetail(
            @Parameter(description = "업종코드", example = "001")
            @PathVariable String sectorCode,
            
            @Parameter(description = "조회시작일 (YYYYMMDD)")
            @RequestParam(required = false) String fromDate,
            
            @Parameter(description = "조회종료일 (YYYYMMDD)")
            @RequestParam(required = false) String toDate,
            
            @Parameter(description = "조회일수 (기본: 30일)", example = "30")
            @RequestParam(required = false) Integer days,
            
            @Parameter(description = "분석유형 (trend:추세분석, distribution:종목분포분석)")
            @RequestParam(required = false) String analysisType) {
        
        log.info("업종일별상세 조회 요청: 업종코드={}, 분석유형={}", sectorCode, analysisType);
        
        // 분석 유형별 특화 조회
        if (analysisType != null) {
            switch (analysisType.toLowerCase()) {
                case "trend":
                    return sectorDailyDetailService.getMediumTermTrendData(sectorCode);
                case "distribution":
                    return sectorDailyDetailService.getStockDistributionAnalysisData(sectorCode);
                default:
                    break;
            }
        }
        
        // 일수 기준 조회
        if (days != null && days > 0) {
            return sectorDailyDetailService.getRecentDailyDetail(sectorCode, days);
        }
        
        // 기간 지정 조회
        if (fromDate != null && toDate != null) {
            return sectorDailyDetailService.getDailyDetailForPeriod(sectorCode, fromDate, toDate);
        }
        
        // 기본 조회 (최근 30일)
        return sectorDailyDetailService.getRecentDailyDetail(sectorCode, 30);
    }
    
    // ========== 편의 메서드 API ==========
    
    @Operation(
        summary = "KOSPI 업종 현황",
        description = "KOSPI 주요 업종들의 현재가 정보를 조회합니다.",
        tags = {"편의 API"}
    )
    @GetMapping(value = "/kospi/overview", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<AllSectorIndicesResponse> getKospiOverview() {
        return allSectorIndicesService.getAllSectorIndices("0", "1", "1", "1");
    }
    
    @Operation(
        summary = "KOSDAQ 업종 현황",
        description = "KOSDAQ 주요 업종들의 현재가 정보를 조회합니다.",
        tags = {"편의 API"}
    )
    @GetMapping(value = "/kosdaq/overview", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<AllSectorIndicesResponse> getKosdaqOverview() {
        return allSectorIndicesService.getAllSectorIndices("1", "1", "1", "1");
    }
    
    @Operation(
        summary = "오늘의 업종 순위",
        description = "당일 업종별 등락률 순위를 조회합니다.",
        tags = {"편의 API"}
    )
    @GetMapping(value = "/ranking/today", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<AllSectorIndicesResponse> getTodayRanking(
            @Parameter(description = "순위유형 (gainers:상승률순, losers:하락률순, volume:거래량순)")
            @RequestParam(defaultValue = "gainers") String rankingType) {
        
        switch (rankingType.toLowerCase()) {
            case "gainers":
                return allSectorIndicesService.getAllSectorIndices("9", "2", "1", "1"); // 등락률 내림차순
            case "losers":
                return allSectorIndicesService.getAllSectorIndices("9", "2", "2", "1"); // 등락률 오름차순
            case "volume":
                return allSectorIndicesService.getAllSectorIndices("9", "3", "1", "1"); // 거래량 내림차순
            default:
                return allSectorIndicesService.getAllSectorIndices("9", "1", "1", "1"); // 지수순
        }
    }
    
    @Operation(
        summary = "실시간 장중 동향",
        description = "현재 시간 기준 장중 업종 동향을 조회합니다.",
        tags = {"편의 API"}
    )
    @GetMapping(value = "/realtime/trend/{sectorCode}", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<SectorMinuteChartResponse> getRealtimeTrend(
            @Parameter(description = "업종코드", example = "001")
            @PathVariable String sectorCode) {
        
        // 5분봉 실시간 차트로 장중 동향 파악
        return sectorMinuteChartService.getRealTimeMinuteChart(sectorCode, 5);
    }
}