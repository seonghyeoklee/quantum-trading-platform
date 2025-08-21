package com.quantum.api.kiwoom.service.chart;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.chart.timeseries.WeeklyChartRequest;
import com.quantum.api.kiwoom.dto.chart.timeseries.WeeklyChartResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 주봉 차트 서비스
 * 키움증권 주식주봉차트조회요청 (ka10082) 처리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class WeeklyChartService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenCacheService;
    
    /**
     * 주봉 차트 데이터 조회 (토큰 자동 관리)
     */
    public Mono<WeeklyChartResponse> getWeeklyChart(String stockCode, String baseDate) {
        log.info("주봉 차트 조회 시작 - 종목: {}, 기준일: {}", stockCode, baseDate);
        
        WeeklyChartRequest request = WeeklyChartRequest.of(stockCode, baseDate);
        request.validate();
        
        return getTokenAndCallApi(request)
                .doOnSuccess(response -> {
                    if (response != null && response.isSuccess()) {
                        log.info("주봉 차트 조회 성공 - 종목: {}, 데이터 수: {}", 
                                stockCode, response.getDataSize());
                    } else {
                        log.warn("주봉 차트 조회 실패 - 종목: {}, 오류: {}", 
                                stockCode, response != null ? response.getErrorMessage() : "null response");
                    }
                })
                .onErrorMap(error -> {
                    log.error("주봉 차트 조회 예외 - 종목: {}", stockCode, error);
                    return new RuntimeException("주봉 차트 조회에 실패했습니다: " + error.getMessage(), error);
                });
    }
    
    /**
     * 주봉 차트 데이터 조회 (LocalDate 기준일)
     */
    public Mono<WeeklyChartResponse> getWeeklyChart(String stockCode, LocalDate baseDate) {
        String baseDateStr = baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        return getWeeklyChart(stockCode, baseDateStr);
    }
    
    /**
     * 오늘 기준 주봉 차트 데이터 조회
     */
    public Mono<WeeklyChartResponse> getWeeklyChartToday(String stockCode) {
        return getWeeklyChart(stockCode, LocalDate.now());
    }
    
    /**
     * 주봉 차트 데이터 조회 (연속조회 지원)
     */
    public Mono<WeeklyChartResponse> getWeeklyChart(String stockCode, String baseDate, String contYn, String nextKey) {
        log.info("주봉 차트 연속조회 - 종목: {}, 기준일: {}, 연속: {}", stockCode, baseDate, contYn);
        
        WeeklyChartRequest request = WeeklyChartRequest.of(stockCode, baseDate);
        request.validate();
        
        return getTokenAndCallApi(request, contYn, nextKey);
    }
    
    /**
     * 특정 토큰으로 주봉 차트 조회 (테스트용)
     */
    public Mono<WeeklyChartResponse> getWeeklyChartWithToken(String accessToken, String stockCode, String baseDate) {
        log.debug("지정 토큰으로 주봉 차트 조회 - 종목: {}, 기준일: {}", stockCode, baseDate);
        
        WeeklyChartRequest request = WeeklyChartRequest.of(stockCode, baseDate);
        request.validate();
        
        return kiwoomApiClient.callChartApi(accessToken, request, WeeklyChartResponse.class);
    }
    
    /**
     * 주봉 차트 조회 (수정주가구분 지정)
     */
    public Mono<WeeklyChartResponse> getWeeklyChart(String stockCode, String baseDate, String updStkpcTp) {
        log.info("주봉 차트 조회 (수정주가구분) - 종목: {}, 기준일: {}, 수정주가: {}", 
                stockCode, baseDate, updStkpcTp);
        
        WeeklyChartRequest request = WeeklyChartRequest.builder()
                .stockCode(stockCode)
                .baseDate(baseDate)
                .updStkpcTp(updStkpcTp)
                .build();
        request.validate();
        
        return getTokenAndCallApi(request);
    }
    
    // ===== Private Methods =====
    
    /**
     * 토큰 조회 및 API 호출
     */
    private Mono<WeeklyChartResponse> getTokenAndCallApi(WeeklyChartRequest request) {
        return getTokenAndCallApi(request, "N", "");
    }
    
    /**
     * 토큰 조회 및 API 호출 (연속조회 지원)
     */
    private Mono<WeeklyChartResponse> getTokenAndCallApi(WeeklyChartRequest request, String contYn, String nextKey) {
        // 환경변수에서 설정된 기본 키를 사용하여 캐시된 토큰 조회
        return tokenCacheService.getCachedToken("default")
                .switchIfEmpty(Mono.error(new IllegalStateException("캐시된 토큰을 찾을 수 없습니다")))
                .flatMap(cachedToken -> {
                    if (cachedToken.isExpired()) {
                        return Mono.error(new IllegalStateException("토큰이 만료되었습니다"));
                    }
                    
                    String accessToken = cachedToken.getToken();
                    return kiwoomApiClient.callChartApi(accessToken, request, WeeklyChartResponse.class, contYn, nextKey);
                });
    }
}