package com.quantum.api.kiwoom.service.chart;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.chart.timeseries.MinuteChartRequest;
import com.quantum.api.kiwoom.dto.chart.timeseries.MinuteChartResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 분봉 차트 서비스
 * 키움증권 주식분봉차트조회요청 (ka10080) 처리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class MinuteChartService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenCacheService;
    
    /**
     * 분봉 차트 데이터 조회 (토큰 자동 관리) - 5분봉 기본
     */
    public Mono<MinuteChartResponse> getMinuteChart(String stockCode, String baseDate) {
        return getMinuteChart(stockCode, baseDate, "5");
    }
    
    /**
     * 분봉 차트 데이터 조회 (토큰 자동 관리)
     */
    public Mono<MinuteChartResponse> getMinuteChart(String stockCode, String baseDate, String ticScope) {
        log.info("분봉 차트 조회 시작 - 종목: {}, 기준일: {}, 분봉: {}분", stockCode, baseDate, ticScope);
        
        MinuteChartRequest request = MinuteChartRequest.of(stockCode, baseDate, ticScope);
        request.validate();
        
        return getTokenAndCallApi(request)
                .doOnSuccess(response -> {
                    if (response != null && response.isSuccess()) {
                        log.info("분봉 차트 조회 성공 - 종목: {}, {}분봉, 데이터 수: {}", 
                                stockCode, ticScope, response.getDataSize());
                    } else {
                        log.warn("분봉 차트 조회 실패 - 종목: {}, {}분봉, 오류: {}", 
                                stockCode, ticScope, response != null ? response.getErrorMessage() : "null response");
                    }
                })
                .onErrorMap(error -> {
                    log.error("분봉 차트 조회 예외 - 종목: {}, {}분봉", stockCode, ticScope, error);
                    return new RuntimeException("분봉 차트 조회에 실패했습니다: " + error.getMessage(), error);
                });
    }
    
    /**
     * 분봉 차트 데이터 조회 (LocalDate 기준일) - 5분봉 기본
     */
    public Mono<MinuteChartResponse> getMinuteChart(String stockCode, LocalDate baseDate) {
        return getMinuteChart(stockCode, baseDate, "5");
    }
    
    /**
     * 분봉 차트 데이터 조회 (LocalDate 기준일)
     */
    public Mono<MinuteChartResponse> getMinuteChart(String stockCode, LocalDate baseDate, String ticScope) {
        String baseDateStr = baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        return getMinuteChart(stockCode, baseDateStr, ticScope);
    }
    
    /**
     * 오늘 기준 분봉 차트 데이터 조회 - 5분봉 기본
     */
    public Mono<MinuteChartResponse> getMinuteChartToday(String stockCode) {
        return getMinuteChart(stockCode, LocalDate.now(), "5");
    }
    
    /**
     * 오늘 기준 분봉 차트 데이터 조회
     */
    public Mono<MinuteChartResponse> getMinuteChartToday(String stockCode, String ticScope) {
        return getMinuteChart(stockCode, LocalDate.now(), ticScope);
    }
    
    /**
     * 분봉 차트 데이터 조회 (연속조회 지원)
     */
    public Mono<MinuteChartResponse> getMinuteChart(String stockCode, String baseDate, String ticScope, 
                                                   String contYn, String nextKey) {
        log.info("분봉 차트 연속조회 - 종목: {}, 기준일: {}, {}분봉, 연속: {}", stockCode, baseDate, ticScope, contYn);
        
        MinuteChartRequest request = MinuteChartRequest.of(stockCode, baseDate, ticScope);
        request.validate();
        
        return getTokenAndCallApi(request, contYn, nextKey);
    }
    
    /**
     * 특정 토큰으로 분봉 차트 조회 (테스트용)
     */
    public Mono<MinuteChartResponse> getMinuteChartWithToken(String accessToken, String stockCode, 
                                                           String baseDate, String ticScope) {
        log.debug("지정 토큰으로 분봉 차트 조회 - 종목: {}, 기준일: {}, {}분봉", stockCode, baseDate, ticScope);
        
        MinuteChartRequest request = MinuteChartRequest.of(stockCode, baseDate, ticScope);
        request.validate();
        
        return kiwoomApiClient.callChartApi(accessToken, request, MinuteChartResponse.class);
    }
    
    /**
     * 분봉 차트 조회 (수정주가구분 지정)
     */
    public Mono<MinuteChartResponse> getMinuteChart(String stockCode, String baseDate, String ticScope, String updStkpcTp) {
        log.info("분봉 차트 조회 (수정주가구분) - 종목: {}, 기준일: {}, {}분봉, 수정주가: {}", 
                stockCode, baseDate, ticScope, updStkpcTp);
        
        MinuteChartRequest request = MinuteChartRequest.builder()
                .stockCode(stockCode)
                .baseDate(baseDate)
                .ticScope(ticScope)
                .updStkpcTp(updStkpcTp)
                .build();
        request.validate();
        
        return getTokenAndCallApi(request);
    }
    
    // ===== 편의 메서드 - 다양한 분봉 타입별 =====
    
    /**
     * 1분봉 차트 조회
     */
    public Mono<MinuteChartResponse> getOneMinuteChart(String stockCode, String baseDate) {
        return getMinuteChart(stockCode, baseDate, "1");
    }
    
    /**
     * 3분봉 차트 조회
     */
    public Mono<MinuteChartResponse> getThreeMinuteChart(String stockCode, String baseDate) {
        return getMinuteChart(stockCode, baseDate, "3");
    }
    
    /**
     * 5분봉 차트 조회
     */
    public Mono<MinuteChartResponse> getFiveMinuteChart(String stockCode, String baseDate) {
        return getMinuteChart(stockCode, baseDate, "5");
    }
    
    /**
     * 10분봉 차트 조회
     */
    public Mono<MinuteChartResponse> getTenMinuteChart(String stockCode, String baseDate) {
        return getMinuteChart(stockCode, baseDate, "10");
    }
    
    /**
     * 15분봉 차트 조회
     */
    public Mono<MinuteChartResponse> getFifteenMinuteChart(String stockCode, String baseDate) {
        return getMinuteChart(stockCode, baseDate, "15");
    }
    
    /**
     * 30분봉 차트 조회
     */
    public Mono<MinuteChartResponse> getThirtyMinuteChart(String stockCode, String baseDate) {
        return getMinuteChart(stockCode, baseDate, "30");
    }
    
    /**
     * 60분봉 차트 조회
     */
    public Mono<MinuteChartResponse> getSixtyMinuteChart(String stockCode, String baseDate) {
        return getMinuteChart(stockCode, baseDate, "60");
    }
    
    // ===== Private Methods =====
    
    /**
     * 토큰 조회 및 API 호출
     */
    private Mono<MinuteChartResponse> getTokenAndCallApi(MinuteChartRequest request) {
        return getTokenAndCallApi(request, "N", "");
    }
    
    /**
     * 토큰 조회 및 API 호출 (연속조회 지원)
     */
    private Mono<MinuteChartResponse> getTokenAndCallApi(MinuteChartRequest request, String contYn, String nextKey) {
        // 환경변수에서 설정된 기본 키를 사용하여 캐시된 토큰 조회
        return tokenCacheService.getCachedToken("default")
                .switchIfEmpty(Mono.error(new IllegalStateException("캐시된 토큰을 찾을 수 없습니다")))
                .flatMap(cachedToken -> {
                    if (cachedToken.isExpired()) {
                        return Mono.error(new IllegalStateException("토큰이 만료되었습니다"));
                    }
                    
                    String accessToken = cachedToken.getToken();
                    return kiwoomApiClient.callChartApi(accessToken, request, MinuteChartResponse.class, contYn, nextKey);
                });
    }
}