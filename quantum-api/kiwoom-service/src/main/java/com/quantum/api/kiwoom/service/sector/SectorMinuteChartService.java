package com.quantum.api.kiwoom.service.sector;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.sector.chart.SectorMinuteChartRequest;
import com.quantum.api.kiwoom.dto.sector.chart.SectorMinuteChartResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

/**
 * 업종분봉조회 서비스 (ka20005)
 * 업종의 분봉 차트 데이터를 조회하는 서비스
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class SectorMinuteChartService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenService;
    
    private static final String TOKEN_KEY = "default";
    
    /**
     * 업종 분봉 차트 조회 (기본)
     */
    public Mono<SectorMinuteChartResponse> getSectorMinuteChart(SectorMinuteChartRequest request) {
        return getSectorMinuteChart(request, null, null);
    }
    
    /**
     * 업종 분봉 차트 조회 (연속조회 지원)
     */
    public Mono<SectorMinuteChartResponse> getSectorMinuteChart(SectorMinuteChartRequest request, 
                                                                String contYn, String nextKey) {
        log.debug("업종분봉조회 요청: 업종코드={}, 분봉구분={}분, 시작일자={}, 종료일자={}", 
                  request.getSectorCode(), request.getMinuteType(), 
                  request.getFromDate(), request.getToDate());
        
        return tokenService.getCachedToken("default")
                .switchIfEmpty(Mono.error(new IllegalStateException("캐시된 토큰을 찾을 수 없습니다")))
                .flatMap(cachedToken -> {
                    if (cachedToken.isExpired()) {
                        return Mono.error(new IllegalStateException("토큰이 만료되었습니다"));
                    }
                    
                    String accessToken = cachedToken.getToken();
                    return kiwoomApiClient.callSectorApi(
                            accessToken, request, SectorMinuteChartResponse.class, contYn, nextKey);
                })
                .doOnSuccess(response -> log.debug("업종분봉조회 응답: 캔들수={}", response.getCandleCount()))
                .doOnError(error -> log.error("업종분봉조회 실패: {}", error.getMessage()));
    }
    
    /**
     * 1분봉 차트 조회
     */
    public Mono<SectorMinuteChartResponse> getOneMinuteChart(String sectorCode) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.oneMinuteChart(sectorCode)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 1분봉 차트 조회 (기간 지정)
     */
    public Mono<SectorMinuteChartResponse> getOneMinuteChart(String sectorCode, String fromDate, String toDate) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.oneMinuteChart(sectorCode)
                .fromDate(fromDate)
                .toDate(toDate)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 5분봉 차트 조회
     */
    public Mono<SectorMinuteChartResponse> getFiveMinuteChart(String sectorCode) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.fiveMinuteChart(sectorCode)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 5분봉 차트 조회 (기간 지정)
     */
    public Mono<SectorMinuteChartResponse> getFiveMinuteChart(String sectorCode, String fromDate, String toDate) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.fiveMinuteChart(sectorCode)
                .fromDate(fromDate)
                .toDate(toDate)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 30분봉 차트 조회
     */
    public Mono<SectorMinuteChartResponse> getThirtyMinuteChart(String sectorCode) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.thirtyMinuteChart(sectorCode)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 30분봉 차트 조회 (기간 지정)
     */
    public Mono<SectorMinuteChartResponse> getThirtyMinuteChart(String sectorCode, String fromDate, String toDate) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.thirtyMinuteChart(sectorCode)
                .fromDate(fromDate)
                .toDate(toDate)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 60분봉(시간봉) 차트 조회
     */
    public Mono<SectorMinuteChartResponse> getHourlyChart(String sectorCode) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.hourlyChart(sectorCode)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 60분봉(시간봉) 차트 조회 (기간 지정)
     */
    public Mono<SectorMinuteChartResponse> getHourlyChart(String sectorCode, String fromDate, String toDate) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.hourlyChart(sectorCode)
                .fromDate(fromDate)
                .toDate(toDate)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 특정 분봉 차트 조회 (사용자 정의)
     */
    public Mono<SectorMinuteChartResponse> getCustomMinuteChart(String sectorCode, Integer minuteType) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.withSectorCode(sectorCode)
                .minuteType(minuteType)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 특정 분봉 차트 조회 (기간 지정)
     */
    public Mono<SectorMinuteChartResponse> getCustomMinuteChart(String sectorCode, Integer minuteType, 
                                                                String fromDate, String toDate) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.withSectorCode(sectorCode)
                .minuteType(minuteType)
                .fromDate(fromDate)
                .toDate(toDate)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 특정 분봉 차트 조회 (시간 범위 지정)
     */
    public Mono<SectorMinuteChartResponse> getCustomMinuteChart(String sectorCode, Integer minuteType,
                                                                String fromDate, String fromTime, 
                                                                String toDate, String toTime) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.withSectorCode(sectorCode)
                .minuteType(minuteType)
                .fromDate(fromDate)
                .fromTime(fromTime)
                .toDate(toDate)
                .toTime(toTime)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 오늘 분봉 차트 조회
     */
    public Mono<SectorMinuteChartResponse> getTodayMinuteChart(String sectorCode, Integer minuteType) {
        String today = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        SectorMinuteChartRequest request = SectorMinuteChartRequest.withSectorCode(sectorCode)
                .minuteType(minuteType)
                .fromDate(today)
                .toDate(today)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 최근 N일간 분봉 차트 조회
     */
    public Mono<SectorMinuteChartResponse> getRecentMinuteChart(String sectorCode, Integer minuteType, int days) {
        LocalDate today = LocalDate.now();
        LocalDate fromDate = today.minusDays(days - 1);
        
        String fromDateStr = fromDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String toDateStr = today.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        
        SectorMinuteChartRequest request = SectorMinuteChartRequest.withSectorCode(sectorCode)
                .minuteType(minuteType)
                .fromDate(fromDateStr)
                .toDate(toDateStr)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 장중 실시간 분봉 차트 조회 (현재 시간까지)
     */
    public Mono<SectorMinuteChartResponse> getRealTimeMinuteChart(String sectorCode, Integer minuteType) {
        String today = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String currentTime = LocalTime.now().format(DateTimeFormatter.ofPattern("HHmmss"));
        
        SectorMinuteChartRequest request = SectorMinuteChartRequest.withSectorCode(sectorCode)
                .minuteType(minuteType)
                .fromDate(today)
                .fromTime("090000") // 장 시작 시간
                .toDate(today)
                .toTime(currentTime)
                .build();
        return getSectorMinuteChart(request);
    }
    
    /**
     * 프리마켓/애프터마켓 포함 분봉 차트 조회
     */
    public Mono<SectorMinuteChartResponse> getExtendedMinuteChart(String sectorCode, Integer minuteType, String date) {
        SectorMinuteChartRequest request = SectorMinuteChartRequest.withSectorCode(sectorCode)
                .minuteType(minuteType)
                .fromDate(date)
                .fromTime("080000") // 프리마켓 시작
                .toDate(date)
                .toTime("180000") // 애프터마켓 종료
                .build();
        return getSectorMinuteChart(request);
    }
}