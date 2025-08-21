package com.quantum.api.kiwoom.service.sector;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.sector.info.SectorDailyDetailRequest;
import com.quantum.api.kiwoom.dto.sector.info.SectorDailyDetailResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 업종현재가일별 서비스 (ka20009)
 * 업종의 일별 상세 현재가 데이터를 조회하는 서비스
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class SectorDailyDetailService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenService;
    
    private static final String TOKEN_KEY = "default";
    
    /**
     * 업종 일별 상세 데이터 조회 (기본)
     */
    public Mono<SectorDailyDetailResponse> getSectorDailyDetail(SectorDailyDetailRequest request) {
        return getSectorDailyDetail(request, null, null);
    }
    
    /**
     * 업종 일별 상세 데이터 조회 (연속조회 지원)
     */
    public Mono<SectorDailyDetailResponse> getSectorDailyDetail(SectorDailyDetailRequest request, 
                                                                String contYn, String nextKey) {
        log.debug("업종현재가일별조회 요청: 업종코드={}, 시작일자={}, 종료일자={}", 
                  request.getSectorCode(), request.getFromDate(), request.getToDate());
        
        return tokenService.getCachedToken("default")
                .switchIfEmpty(Mono.error(new IllegalStateException("캐시된 토큰을 찾을 수 없습니다")))
                .flatMap(cachedToken -> {
                    if (cachedToken.isExpired()) {
                        return Mono.error(new IllegalStateException("토큰이 만료되었습니다"));
                    }
                    
                    String accessToken = cachedToken.getToken();
                    return kiwoomApiClient.callSectorApi(
                            accessToken, request, SectorDailyDetailResponse.class, contYn, nextKey);
                })
                .doOnSuccess(response -> log.debug("업종현재가일별조회 응답: 데이터수={}", response.getDataCount()))
                .doOnError(error -> log.error("업종현재가일별조회 실패: {}", error.getMessage()));
    }
    
    /**
     * 기간별 일별 상세 데이터 조회
     */
    public Mono<SectorDailyDetailResponse> getDailyDetailForPeriod(String sectorCode, String fromDate, String toDate) {
        SectorDailyDetailRequest request = SectorDailyDetailRequest.forPeriod(sectorCode, fromDate, toDate)
                .build();
        return getSectorDailyDetail(request);
    }
    
    /**
     * 최근 N일간 일별 상세 데이터 조회
     */
    public Mono<SectorDailyDetailResponse> getRecentDailyDetail(String sectorCode, int days) {
        LocalDate today = LocalDate.now();
        LocalDate fromDate = today.minusDays(days - 1);
        
        String fromDateStr = fromDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyDetailForPeriod(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 금주 일별 상세 데이터 조회
     */
    public Mono<SectorDailyDetailResponse> getThisWeekDailyDetail(String sectorCode) {
        LocalDate today = LocalDate.now();
        LocalDate mondayOfThisWeek = today.minusDays(today.getDayOfWeek().getValue() - 1);
        
        String fromDateStr = mondayOfThisWeek.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyDetailForPeriod(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 금월 일별 상세 데이터 조회
     */
    public Mono<SectorDailyDetailResponse> getThisMonthDailyDetail(String sectorCode) {
        LocalDate today = LocalDate.now();
        LocalDate firstDayOfMonth = today.withDayOfMonth(1);
        
        String fromDateStr = firstDayOfMonth.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyDetailForPeriod(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 금년 일별 상세 데이터 조회
     */
    public Mono<SectorDailyDetailResponse> getYearToDateDailyDetail(String sectorCode) {
        LocalDate today = LocalDate.now();
        LocalDate yearStart = LocalDate.of(today.getYear(), 1, 1);
        
        String fromDateStr = yearStart.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyDetailForPeriod(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 특정 연도 일별 상세 데이터 조회
     */
    public Mono<SectorDailyDetailResponse> getYearlyDailyDetail(String sectorCode, int year) {
        LocalDate yearStart = LocalDate.of(year, 1, 1);
        LocalDate yearEnd = LocalDate.of(year, 12, 31);
        
        String fromDateStr = yearStart.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = yearEnd.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyDetailForPeriod(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 특정 월 일별 상세 데이터 조회
     */
    public Mono<SectorDailyDetailResponse> getMonthlyDailyDetail(String sectorCode, int year, int month) {
        LocalDate monthStart = LocalDate.of(year, month, 1);
        LocalDate monthEnd = monthStart.withDayOfMonth(monthStart.lengthOfMonth());
        
        String fromDateStr = monthStart.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = monthEnd.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyDetailForPeriod(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 분기별 일별 상세 데이터 조회
     */
    public Mono<SectorDailyDetailResponse> getQuarterlyDailyDetail(String sectorCode, int year, int quarter) {
        if (quarter < 1 || quarter > 4) {
            throw new IllegalArgumentException("분기는 1~4 사이의 값이어야 합니다.");
        }
        
        int startMonth = (quarter - 1) * 3 + 1;
        LocalDate quarterStart = LocalDate.of(year, startMonth, 1);
        LocalDate quarterEnd = quarterStart.plusMonths(2).withDayOfMonth(quarterStart.plusMonths(2).lengthOfMonth());
        
        String fromDateStr = quarterStart.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = quarterEnd.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyDetailForPeriod(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 연속조회를 통한 대용량 데이터 조회
     */
    public Mono<SectorDailyDetailResponse> getLargePeriodDailyDetail(String sectorCode, String fromDate, 
                                                                     String toDate, String continuationKey) {
        SectorDailyDetailRequest request = SectorDailyDetailRequest.withContinuation(
                sectorCode, fromDate, toDate, continuationKey).build();
        return getSectorDailyDetail(request, "Y", continuationKey);
    }
    
    /**
     * 커스텀 기간 일별 상세 데이터 조회 (LocalDate 사용)
     */
    public Mono<SectorDailyDetailResponse> getCustomDailyDetail(String sectorCode, LocalDate fromDate, LocalDate toDate) {
        String fromDateStr = fromDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = toDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        return getDailyDetailForPeriod(sectorCode, fromDateStr, toDateStr);
    }
    
    /**
     * 단기 추세 분석용 데이터 조회 (최근 5일)
     */
    public Mono<SectorDailyDetailResponse> getShortTermTrendData(String sectorCode) {
        return getRecentDailyDetail(sectorCode, 5);
    }
    
    /**
     * 중기 추세 분석용 데이터 조회 (최근 20일)
     */
    public Mono<SectorDailyDetailResponse> getMediumTermTrendData(String sectorCode) {
        return getRecentDailyDetail(sectorCode, 20);
    }
    
    /**
     * 장기 추세 분석용 데이터 조회 (최근 60일)
     */
    public Mono<SectorDailyDetailResponse> getLongTermTrendData(String sectorCode) {
        return getRecentDailyDetail(sectorCode, 60);
    }
    
    /**
     * 종목 분포 분석용 데이터 조회 (최근 30일)
     */
    public Mono<SectorDailyDetailResponse> getStockDistributionAnalysisData(String sectorCode) {
        return getRecentDailyDetail(sectorCode, 30);
    }
    
    /**
     * 코로나19 영향 분석용 데이터 조회 (2020년 1월~현재)
     */
    public Mono<SectorDailyDetailResponse> getCovidImpactAnalysisData(String sectorCode) {
        LocalDate covidStart = LocalDate.of(2020, 1, 1);
        LocalDate today = LocalDate.now();
        
        return getCustomDailyDetail(sectorCode, covidStart, today);
    }
}