package com.quantum.api.kiwoom.service.sector;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.sector.chart.SectorDailyChartRequest;
import com.quantum.api.kiwoom.dto.sector.chart.SectorDailyChartResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 업종일봉조회 서비스 (ka20006)
 * 업종의 일봉 차트 데이터를 조회하는 서비스
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class SectorDailyChartService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenService;
    
    private static final String TOKEN_KEY = "default";
    
    /**
     * 업종 일봉 차트 조회 (기본)
     */
    public Mono<SectorDailyChartResponse> getSectorDailyChart(SectorDailyChartRequest request) {
        return getSectorDailyChart(request, null, null);
    }
    
    /**
     * 업종 일봉 차트 조회 (연속조회 지원)
     */
    public Mono<SectorDailyChartResponse> getSectorDailyChart(SectorDailyChartRequest request, 
                                                              String contYn, String nextKey) {
        log.debug("업종일봉조회 요청: 업종코드={}, 시작일자={}, 종료일자={}, 기간분류={}", 
                  request.getSectorCode(), request.getFromDate(), 
                  request.getToDate(), request.getPeriodType());
        
        return tokenService.getCachedToken("default")
                .switchIfEmpty(Mono.error(new IllegalStateException("캐시된 토큰을 찾을 수 없습니다")))
                .flatMap(cachedToken -> {
                    if (cachedToken.isExpired()) {
                        return Mono.error(new IllegalStateException("토큰이 만료되었습니다"));
                    }
                    
                    String accessToken = cachedToken.getToken();
                    return kiwoomApiClient.callSectorApi(
                            accessToken, request, SectorDailyChartResponse.class, contYn, nextKey);
                })
                .doOnSuccess(response -> log.debug("업종일봉조회 응답: 캔들수={}", response.getCandleCount()))
                .doOnError(error -> log.error("업종일봉조회 실패: {}", error.getMessage()));
    }
    
    /**
     * 일봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getDailyChart(String sectorCode, String fromDate, String toDate) {
        SectorDailyChartRequest request = SectorDailyChartRequest.dailyChart(sectorCode, fromDate, toDate)
                .build();
        return getSectorDailyChart(request);
    }
    
    /**
     * 주봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getWeeklyChart(String sectorCode, String fromDate, String toDate) {
        SectorDailyChartRequest request = SectorDailyChartRequest.weeklyChart(sectorCode, fromDate, toDate)
                .build();
        return getSectorDailyChart(request);
    }
    
    /**
     * 월봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getMonthlyChart(String sectorCode, String fromDate, String toDate) {
        SectorDailyChartRequest request = SectorDailyChartRequest.monthlyChart(sectorCode, fromDate, toDate)
                .build();
        return getSectorDailyChart(request);
    }
    
    /**
     * 최근 N일간 일봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getRecentDailyChart(String sectorCode, int days) {
        LocalDate today = LocalDate.now();
        LocalDate fromDate = today.minusDays(days - 1);
        
        String fromDateStr = fromDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyChart(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 최근 N주간 주봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getRecentWeeklyChart(String sectorCode, int weeks) {
        LocalDate today = LocalDate.now();
        LocalDate fromDate = today.minusWeeks(weeks);
        
        String fromDateStr = fromDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getWeeklyChart(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 최근 N개월간 월봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getRecentMonthlyChart(String sectorCode, int months) {
        LocalDate today = LocalDate.now();
        LocalDate fromDate = today.minusMonths(months);
        
        String fromDateStr = fromDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getMonthlyChart(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 금년 일봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getYearToDateChart(String sectorCode) {
        LocalDate today = LocalDate.now();
        LocalDate yearStart = LocalDate.of(today.getYear(), 1, 1);
        
        String fromDateStr = yearStart.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyChart(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 특정 연도 일봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getYearlyChart(String sectorCode, int year) {
        LocalDate yearStart = LocalDate.of(year, 1, 1);
        LocalDate yearEnd = LocalDate.of(year, 12, 31);
        
        String fromDateStr = yearStart.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = yearEnd.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyChart(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 특정 월 일봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getMonthChart(String sectorCode, int year, int month) {
        LocalDate monthStart = LocalDate.of(year, month, 1);
        LocalDate monthEnd = monthStart.withDayOfMonth(monthStart.lengthOfMonth());
        
        String fromDateStr = monthStart.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = monthEnd.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyChart(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 분기별 일봉 차트 조회
     */
    public Mono<SectorDailyChartResponse> getQuarterChart(String sectorCode, int year, int quarter) {
        if (quarter < 1 || quarter > 4) {
            throw new IllegalArgumentException("분기는 1~4 사이의 값이어야 합니다.");
        }
        
        int startMonth = (quarter - 1) * 3 + 1;
        LocalDate quarterStart = LocalDate.of(year, startMonth, 1);
        LocalDate quarterEnd = quarterStart.plusMonths(2).withDayOfMonth(quarterStart.plusMonths(2).lengthOfMonth());
        
        String fromDateStr = quarterStart.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = quarterEnd.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyChart(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 단기 차트 조회 (최근 1주일)
     */
    public Mono<SectorDailyChartResponse> getShortTermChart(String sectorCode) {
        return getRecentDailyChart(sectorCode, 7);
    }
    
    /**
     * 중기 차트 조회 (최근 1개월)
     */
    public Mono<SectorDailyChartResponse> getMediumTermChart(String sectorCode) {
        return getRecentDailyChart(sectorCode, 30);
    }
    
    /**
     * 장기 차트 조회 (최근 3개월)
     */
    public Mono<SectorDailyChartResponse> getLongTermChart(String sectorCode) {
        return getRecentDailyChart(sectorCode, 90);
    }
    
    /**
     * 초장기 차트 조회 (최근 1년)
     */
    public Mono<SectorDailyChartResponse> getVeryLongTermChart(String sectorCode) {
        return getRecentDailyChart(sectorCode, 365);
    }
    
    /**
     * 코로나19 영향 분석용 차트 (2020년 1월~현재)
     */
    public Mono<SectorDailyChartResponse> getCovidImpactChart(String sectorCode) {
        LocalDate covidStart = LocalDate.of(2020, 1, 1);
        LocalDate today = LocalDate.now();
        
        String fromDateStr = covidStart.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyChart(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 특정 기간 커스텀 차트 조회 (LocalDate 사용)
     */
    public Mono<SectorDailyChartResponse> getCustomChart(String sectorCode, LocalDate fromDate, LocalDate toDate, String periodType) {
        String fromDateStr = fromDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = toDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        SectorDailyChartRequest request = SectorDailyChartRequest.withSectorCode(sectorCode)
                .fromDate(fromDateStr)
                .toDate(toDateStr)
                .periodType(periodType)
                .build();
        
        return getSectorDailyChart(request);
    }
}